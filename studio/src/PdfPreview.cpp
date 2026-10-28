#include "PdfPreview.h"

#include <QFileInfo>
#include <QGuiApplication>
#include <QPdfDocument>
#include <QPdfPageNavigator>
#include <QScreen>
#include <QScrollBar>
#include <QShowEvent>
#include <QTimer>
#include <QWheelEvent>

#include <cmath>

PdfPreview::PdfPreview(QWidget *parent) : QPdfView(parent)
{
    setPageMode(PageMode::MultiPage);
    setZoomMode(ZoomMode::FitToWidth);
}

// Ctrl+wheel zooms around the point under the mouse: the same place of the same
// page stays under the cursor. Fit modes need their actual on-screen scale, not
// the stored custom factor.
void PdfPreview::wheelEvent(QWheelEvent *event)
{
    if (!(event->modifiers() & Qt::ControlModifier)) {
        QPdfView::wheelEvent(event);
        return;
    }
    event->accept();
    if (!document() || document()->status() != QPdfDocument::Status::Ready
        || document()->pageCount() == 0) return;
    const QPointF position = event->position();
    const DocumentPoint point = documentPointAt(position);
    if (point.page < 0) return;
    qreal factor = zoomFactor();
    if (zoomMode() != ZoomMode::Custom) {
        const qreal dpi = QGuiApplication::primaryScreen()->logicalDotsPerInch() / 72.0;
        factor = scaledPageSize(point.page).height() / qMax(1.0, document()->pagePointSize(point.page).height() * dpi);
    }
    const qreal steps = event->angleDelta().y() != 0
        ? event->angleDelta().y() / 120.0 : event->pixelDelta().y() / 40.0;
    if (steps == 0) return;
    const qreal next = qBound(0.1, factor * std::pow(1.2, qBound(-8.0, steps, 8.0)), 8.0);
    // A pending restoration (reload, session) must not move the view afterwards.
    ++m_generation;
    m_pending.clear();
    setZoomMode(ZoomMode::Custom);
    setZoomFactor(next);
    scrollPointTo(point, position);
    // The scroll ranges may be updated after the layout pass; repeat once it is done.
    const int generation = m_generation;
    QTimer::singleShot(0, this, [this, point, position, generation] {
        if (generation == m_generation) scrollPointTo(point, position);
    });
}

QPoint PdfPreview::pageOrigin(int page) const
{
    int top = documentMargins().top();
    int widest = 0;
    for (int i = 0; i < document()->pageCount(); ++i) {
        const QSize size = scaledPageSize(i);
        widest = qMax(widest, size.width());
        if (i < page) top += size.height() + pageSpacing();
    }
    // Pages are centred in the document area, which is at least as wide as the viewport.
    const int area = qMax(viewport()->width(), widest + documentMargins().left() + documentMargins().right());
    const int left = documentMargins().left()
        + (area - documentMargins().left() - documentMargins().right() - scaledPageSize(page).width()) / 2;
    return {left, top};
}

PdfPreview::DocumentPoint PdfPreview::documentPointAt(const QPointF &position) const
{
    DocumentPoint point;
    if (!document() || document()->status() != QPdfDocument::Status::Ready || document()->pageCount() == 0)
        return point;
    const qreal y = verticalScrollBar()->value() + position.y();
    const qreal x = horizontalScrollBar()->value() + position.x();
    int page = 0;
    int top = documentMargins().top();
    for (; page + 1 < document()->pageCount(); ++page) {
        const int height = scaledPageSize(page).height();
        if (y < top + height + pageSpacing())
            break;
        top += height + pageSpacing();
    }
    const QSize size = scaledPageSize(page);
    const QPoint origin = pageOrigin(page);
    point.page = page;
    point.y = (y - origin.y()) / qMax(1, size.height());
    point.x = (x - origin.x()) / qMax(1, size.width());
    return point;
}

void PdfPreview::scrollPointTo(const DocumentPoint &point, const QPointF &position)
{
    if (!document() || document()->status() != QPdfDocument::Status::Ready || point.page < 0
        || point.page >= document()->pageCount()) return;
    const QSize size = scaledPageSize(point.page);
    const QPoint origin = pageOrigin(point.page);
    verticalScrollBar()->setValue(qRound(origin.y() + point.y * size.height() - position.y()));
    horizontalScrollBar()->setValue(qRound(origin.x() + point.x * size.width() - position.x()));
}

void PdfPreview::setPdfDocument(QPdfDocument *pdf)
{
    setDocument(pdf);
    connect(pdf, &QPdfDocument::statusChanged, this, [this](QPdfDocument::Status status) {
        if (status == QPdfDocument::Status::Ready)
            scheduleRestore();
    });
}

QSize PdfPreview::scaledPageSize(int page) const
{
    const qreal dpi = QGuiApplication::primaryScreen()->logicalDotsPerInch() / 72.0;
    const QSizeF points = document()->pagePointSize(page);
    if (zoomMode() == ZoomMode::Custom)
        return (points * dpi * zoomFactor()).toSize();
    QSize pixels = (points * dpi).toSize();
    if (zoomMode() == ZoomMode::FitToWidth) {
        const int width = qMax(1, viewport()->width() - documentMargins().left() - documentMargins().right());
        pixels *= qreal(width) / qMax(1, pixels.width());
        return pixels;
    }
    return pixels.scaled(QSize(qMax(1, viewport()->width() - documentMargins().left() - documentMargins().right()),
                              qMax(1, viewport()->height() - pageSpacing())), Qt::KeepAspectRatio);
}

QVariantMap PdfPreview::sessionState() const
{
    if (!m_pending.isEmpty())
        return m_pending;
    if (!document() || document()->status() != QPdfDocument::Status::Ready || document()->pageCount() == 0)
        return {};
    const int scroll = verticalScrollBar()->value();
    int top = documentMargins().top();
    int page = 0;
    for (; page + 1 < document()->pageCount(); ++page) {
        const int height = scaledPageSize(page).height();
        if (scroll < top + height + pageSpacing())
            break;
        top += height + pageSpacing();
    }
    const qreal offset = qreal(scroll - top) / qMax(1, scaledPageSize(page).height());
    return {{QStringLiteral("page"), page}, {QStringLiteral("offset"), offset},
            {QStringLiteral("zoomMode"), int(zoomMode())}, {QStringLiteral("zoom"), zoomFactor()},
            {QStringLiteral("vRatio"), qreal(scroll) / qMax(1, verticalScrollBar()->maximum())},
            {QStringLiteral("hRatio"), qreal(horizontalScrollBar()->value()) / qMax(1, horizontalScrollBar()->maximum())}};
}

void PdfPreview::restoreSessionState(const QVariantMap &state)
{
    ++m_generation;
    m_pending = state;
    if (document() && document()->status() == QPdfDocument::Status::Ready)
        scheduleRestore();
}

void PdfPreview::reload(const QString &path)
{
    QVariantMap state = m_pending;
    if (m_path == path && state.isEmpty())
        state = sessionState();
    ++m_generation;
    m_path = path;
    m_pending = state;
    document()->close();
    if (QFileInfo::exists(path))
        document()->load(path);
}

void PdfPreview::clear()
{
    ++m_generation;
    m_pending.clear();
    m_path.clear();
    document()->close();
    pageNavigator()->clear();
    setZoomMode(ZoomMode::FitToWidth);
}

void PdfPreview::showPage(int page)
{
    QVariantMap state = sessionState();
    if (state.isEmpty())
        state = {{QStringLiteral("zoomMode"), int(zoomMode())}, {QStringLiteral("zoom"), zoomFactor()}};
    state.insert(QStringLiteral("page"), qMax(0, page));
    state.insert(QStringLiteral("offset"), 0.0);
    state.insert(QStringLiteral("hRatio"), 0.0);
    restoreSessionState(state);
}

void PdfPreview::scheduleRestore()
{
    const int generation = m_generation;
    QTimer::singleShot(0, this, [this, generation] {
        if (generation == m_generation)
            applyPendingState();
    });
}

void PdfPreview::applyPendingState()
{
    // A hidden PDF tab has no reliable viewport width; restore when shown.
    if (m_pending.isEmpty() || !isVisible() || !document()
        || document()->status() != QPdfDocument::Status::Ready || document()->pageCount() == 0)
        return;
    const QVariantMap state = m_pending;
    const int mode = qBound(0, state.value(QStringLiteral("zoomMode"), int(ZoomMode::FitToWidth)).toInt(), 2);
    qreal zoom = state.value(QStringLiteral("zoom"), 1.0).toDouble();
    if (!std::isfinite(zoom) || zoom <= 0)
        zoom = 1;
    setZoomFactor(zoom);
    setZoomMode(ZoomMode(mode));
    // Layout/scrollbar ranges may change during the zoom and visibility update.
    const int generation = m_generation;
    QTimer::singleShot(0, this, [this, state, generation] {
        if (generation != m_generation || !isVisible() || document()->status() != QPdfDocument::Status::Ready)
            return;
        const int page = qBound(0, state.value(QStringLiteral("page")).toInt(), document()->pageCount() - 1);
        int top = documentMargins().top();
        for (int i = 0; i < page; ++i)
            top += scaledPageSize(i).height() + pageSpacing();
        qreal offset = state.value(QStringLiteral("offset")).toDouble();
        if (!std::isfinite(offset))
            offset = 0;
        pageNavigator()->jump(page, QPointF(0, offset * document()->pagePointSize(page).height()));
        // Setting the navigator alone restores only the page in Qt 6.4/6.5.
        const int target = top + qRound(qBound(-0.05, offset, 1.0) * scaledPageSize(page).height());
        verticalScrollBar()->setValue(target);
        horizontalScrollBar()->setValue(qRound(state.value(QStringLiteral("hRatio")).toDouble()
                                               * horizontalScrollBar()->maximum()));
        m_pending.clear();
    });
}

void PdfPreview::showEvent(QShowEvent *event)
{
    QPdfView::showEvent(event);
    scheduleRestore();
}
