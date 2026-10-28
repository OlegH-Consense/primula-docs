#pragma once

// The version of Primula Studio (the version of the translator, read from
// ../pyproject.toml when CMake configures the build).  It lives in one generated
// source file (StudioVersion.cpp.in → <build>/generated/StudioVersion.cpp) rather
// than in a compile definition: a version bump then recompiles that file only,
// not every source of Studio and of its tests.

/// The full version string, e.g. "0.1.0.dev46".
const char *studioVersion();
