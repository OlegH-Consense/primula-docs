#pragma once

#include <QPdfView>
#include <QVariantMap>

// QPdfPageNavigator does not track the offset of manual scrolling in all Qt
// versions. Store a page-relative anchor derived from public page metrics.
class PdfPreview : public QPdfView
{
    Q_OBJECT
public:
    explicit PdfPreview(QWidget *parent = nullptr);
    /// Attach the PDF model and restore deferred position when it becomes ready. The caller retains ownership.
    void setPdfDocument(QPdfDocument *document);
    /// Return top page, fractional page offset, zoom and horizontal scroll for persistence.
    QVariantMap sessionState() const;
    /// Queue state restoration; hidden/not-ready views defer it until layout is reliable.
    void restoreSessionState(const QVariantMap &state);
    /// Reload path, retaining the anchor for the same document; newer generations invalidate old callbacks.
    void reload(const QString &path);
    /// Discard document and pending anchor, returning to fit-to-width mode.
    void clear();
    /// Scroll to the top of a page (0-based), keeping the zoom; deferred while hidden.
    void showPage(int page);
    /// The PDF shown (or being loaded), empty when none.
    QString path() const { return m_path; }
    /// The point of the document under a viewport position: page (0-based) and the
    /// fractions of the page width (x) and height (y). Page -1 when no document is ready.
    struct DocumentPoint { int page = -1; qreal x = 0; qreal y = 0; };
    DocumentPoint documentPointAt(const QPointF &position) const;

protected:
    void showEvent(QShowEvent *event) override;
    void wheelEvent(QWheelEvent *event) override;

private:
    QSize scaledPageSize(int page) const;
    /// Top of a page and its left edge in document pixels at the current scale.
    QPoint pageOrigin(int page) const;
    /// Scroll so that point lies under the viewport position.
    void scrollPointTo(const DocumentPoint &point, const QPointF &position);
    void scheduleRestore();
    void applyPendingState();
    QVariantMap m_pending;
    QString m_path;
    int m_generation = 0;
};
