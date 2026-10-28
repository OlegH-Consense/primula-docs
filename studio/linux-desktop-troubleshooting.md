# Linux: desktop, KDE/Wayland и сообщения запуска


The native KDE file dialog can print `kf.kio.widgets.kdirmodel: No node found`
while refreshing or filtering a directory. The listed paths are directory-model
entries; this message does not mean that Studio reads their file contents.
Studio 0.3.2 starts new-project browsing from its process working directory and
reuses the most recently selected directory between wizard fields.

`BASH_FUNC_*` messages mean that KIO refuses to forward an exported Bash
function whose environment name is invalid for systemd. Mouse-grab messages
come from the Qt Wayland platform plugin. These diagnostics are not Studio
build errors and are intentionally not hidden by application-wide logging
filters.


## Desktop metadata


`build-and-run-studio.sh` registers the build's absolute executable/icon paths in
`$XDG_DATA_HOME/applications` (default `~/.local/share/applications`). It leaves
an existing installed Studio entry in place. `install-local.sh` updates that
entry to the installed executable. No root privileges are required.

For a binary launched directly after a build, first run:

```bash
studio/register-desktop.sh --build
```

This makes `org.primula_docs.Studio.desktop` visible to the separate host portal.
Changing only the application's `XDG_DATA_DIRS` cannot guarantee discovery by
an already running portal service. Move the build directory only after updating
its registration. The native Wayland icon and portal behavior need field testing.
Reference: <https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.host.portal.Registry.html>.

