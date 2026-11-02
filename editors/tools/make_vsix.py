#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка пакета расширения VS Code / Cursor / VSCodium: vscode/primula-<версия>.vsix.

Зачем: современный VS Code и Cursor не подхватывают расширения, просто скопированные в
~/.vscode/extensions или ~/.cursor/extensions: они должны быть перечислены в extensions.json,
а его ведёт сама программа при установке. Правильный путь — пакет .vsix и команда
`code --install-extension primula-0.1.0.vsix` (или `cursor …`, `codium …`).

VSIX — обычный zip: [Content_Types].xml, extension.vsixmanifest и каталог extension/ с файлами
расширения. Сборка детерминирована (фиксированные даты и порядок), поэтому тест проекта
сравнивает пакет с исходниками. Формат: https://github.com/microsoft/vscode-vsce (папка src/package.ts)
и описание манифеста VSIX Visual Studio Marketplace.

Запуск: python3 make_vsix.py [каталог_vscode]   (по умолчанию ../vscode)
"""
import json
import os
import sys
import zipfile
from xml.sax.saxutils import quoteattr

DATE = (2026, 1, 1, 0, 0, 0)
FILES = ("package.json", "language-configuration.json",
         "syntaxes/primula.tmLanguage.json", "syntaxes/primula-code.tmLanguage.json")


def build(folder):
    """Пакет .vsix из каталога расширения.

    Args:
        folder: каталог vscode/ (package.json и syntaxes/).

    Returns:
        (имя_файла, байты).
    """
    manifest = json.load(open(os.path.join(folder, "package.json"), encoding="utf-8"))
    identity = (manifest["publisher"], manifest["name"], manifest["version"])
    content_types = ('<?xml version="1.0" encoding="utf-8"?>\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension=".json" ContentType="application/json"/>'
                     '<Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>\n')
    vsixmanifest = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">'
        '<Metadata><Identity Language="en-US" Id=%s Version=%s Publisher=%s/>'
        '<DisplayName>%s</DisplayName><Description xml:space="preserve">%s</Description>'
        '<Categories>%s</Categories></Metadata>'
        '<Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>'
        '<Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" '
        'Addressable="true"/></Assets></PackageManifest>\n') % (
        quoteattr(identity[1]), quoteattr(identity[2]), quoteattr(identity[0]),
        manifest["displayName"], manifest["description"], ",".join(manifest.get("categories", [])))
    name = "%s-%s.vsix" % (identity[1], identity[2])
    from io import BytesIO
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        def add(path, data):
            info = zipfile.ZipInfo(path, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
        add("[Content_Types].xml", content_types)
        add("extension.vsixmanifest", vsixmanifest)
        for relative in FILES:
            add("extension/" + relative, open(os.path.join(folder, relative), "rb").read())
    return name, buffer.getvalue()


def main(argv):
    folder = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vscode")
    name, data = build(folder)
    path = os.path.join(folder, name)
    with open(path, "wb") as handle:
        handle.write(data)
    print("записан", path)


if __name__ == "__main__":
    main(sys.argv[1:])
