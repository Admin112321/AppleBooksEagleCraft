# AppleBooksEagleCraft

**AppleBooksEagleCraft** is a custom EPUB-port of the Eaglercraft browser-based engine, rebuilt to operate natively within **Apple Books** on iOS, iPadOS, and macOS. This repository includes both the full game HTML and a Python-based build system (`EaglePub.py`) that packages the content into a standards-compliant EPUB format.

This project does not rely on EPUB auto-generators, wrappers, or generic converters. Every element—from file structure to HTML sanitization and metadata management—is crafted explicitly for Apple’s rendering environment.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Build Tool: `EaglePub.py`](#build-tool-eaglepubpy)
  - [Functionality Overview](#functionality-overview)
  - [Code Breakdown](#code-breakdown)
- [Installation and Build](#installation-and-build)
- [How It Works](#how-it-works)
- [EPUB Standards Compliance](#epub-standards-compliance)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**AppleBooksEagleCraft** aims to deliver a complete, self-contained Eaglercraft gameplay experience within an EPUB container. This approach enables:

- Offline play within Apple Books.
- Complete compatibility with EPUB 3.2 rendering specs.
- Reuse of existing web game logic, adapted for embedded environments.

The EPUB includes a launch interface (`index.xhtml`) that loads the game engine in a controlled context, while `EaglePub.py` ensures proper EPUB formatting.

---

## Repository Structure

```
AppleBooksEagleCraft/
├── EaglePub.py               # Python script for EPUB generation
├── eaglecraft.html           # Full HTML game engine (source)
├── assets/                   # Game assets (textures, fonts, sounds)
├── build/                    # Output directory for the final .epub
├── README.md
└── LICENSE
```

---

## Build Tool: `EaglePub.py`

### Functionality Overview

`EaglePub.py` is the heart of this repository's packaging process. It takes your core game HTML (`eaglecraft.html`), injects necessary scripts, generates EPUB navigation metadata, and bundles everything into a valid EPUB container under `~/Documents/eaglecraft_book.epub`.

### Code Breakdown

#### Working Directory Setup

```python
output_dir = os.path.expanduser("~/Documents/eaglepub/")
meta_inf_path = os.path.join(output_dir, "META-INF")
oebps_path = os.path.join(output_dir, "OEBPS")
```

- Creates all required EPUB directory structures (`META-INF`, `OEBPS`) in a temporary location.
- Ensures `os.makedirs(..., exist_ok=True)` prevents failures if rerun.

#### `mimetype` File Creation

```python
with open(mimetype_path, "w") as f:
    f.write("application/epub+zip")
```

- Written uncompressed and first in the ZIP archive to comply with EPUB 3.0+ rules.
- Essential for recognition by EPUB validators and Apple Books.

#### HTML Patching

```python
browser_api_fixes = """
<!-- Placeholder for Web API patches -->
"""
modified_html = html_content.replace("</head>", browser_api_fixes + "</head>")
```

- This injects additional JavaScript or CSS that may be required to make web APIs work inside Apple Books.
- Currently a placeholder—this is where touch input polyfills or CSP-friendly fixes can be inserted.

#### EPUB Entry Interface

```html
<!-- index.xhtml -->
<html xmlns="http://www.w3.org/1999/xhtml" ...>
  <head>
    <title>EagleCraft EPUB</title>
    ...
  </head>
  <body>
    <button onclick="...">Launch Game</button>
    <div id="console">...</div>
  </body>
</html>
```

- Provides a touch-friendly UI with fallback instructions.
- Launch button embeds and loads `eaglecraft_fixed.html`.

#### Metadata and Navigation

```xml
<!-- content.opf -->
<package xmlns="http://www.idpf.org/2007/opf" ...>
  <metadata>
    <dc:title>EagleCraft EPUB</dc:title>
    ...
  </metadata>
  <manifest>
    <item id="main" href="index.xhtml" media-type="application/xhtml+xml"/>
    ...
  </manifest>
  <spine>
    <itemref idref="main"/>
  </spine>
</package>
```

- `content.opf`: Declares spine structure, manifest items, and metadata like UUID and date.
- `toc.ncx` and `nav.xhtml`: Provide table-of-contents support across all EPUB-compliant readers.

#### Packaging

```python
with zipfile.ZipFile(epub_path, "w", ...) as epub:
    epub.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
    ...
```

- Ensures `mimetype` is added first, uncompressed.
- Includes `OEBPS/`, `META-INF/`, and all linked game files.

#### Cleanup

```python
shutil.rmtree(output_dir)
```

- Deletes temporary folders to avoid clutter and reprocessing errors.

---

## Installation and Build

### Prerequisites

- Python 3.6+
- A full `eaglecraft.html` file in the project root
- Apple Books installed on target device (iOS/macOS)

### Steps

```bash
git clone https://github.com/Admin112321/AppleBooksEagleCraft.git
cd AppleBooksEagleCraft
python3 EaglePub.py
```

- Output: `~/Documents/eaglecraft_book.epub`
- Transfer via AirDrop or Finder into Apple Books

---

## How It Works

1. Apple Books opens `index.xhtml`, which contains a launcher interface.
2. The user clicks "Launch Game", which loads the sanitized and injected `eaglecraft_fixed.html` via embedded `<iframe>` or script redirect.
3. All game logic, rendering, and assets operate from within the EPUB’s local file system.
4. Debug messages and logs are shown in the embedded `<div id="console">`.

---

## EPUB Standards Compliance

This project adheres to EPUB 3.2 standards including:

- `mimetype` ordering
- Valid `container.xml` and `content.opf`
- Navigational `toc.ncx` and `nav.xhtml`
- UTF-8 encoded, XHTML-validated content

Tested via:

```bash
epubcheck build/eaglecraft_book.epub
```

---

## Known Limitations

- Apple Books does not support all modern JavaScript APIs (e.g. WebGL2).
- Performance may degrade on older iPads or Intel Macs.
- Mouseover or hover-based UI elements may not work without touch adaptation.

---

## Contributing

1. Fork this repository
2. Create a new feature branch: `feature/your-feature`
3. Run and validate EPUB via `EaglePub.py`
4. Submit a pull request with documentation if possible

All contributions must preserve EPUB standards compliance and be tested on Apple Books.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
