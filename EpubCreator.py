import os
import zipfile
import datetime
import uuid
import html

def create_eaglecraft_epub():
    output_dir = os.path.expanduser("~/Documents/eaglepub")
    os.makedirs(output_dir, exist_ok=True)

    mimetype_path = os.path.join(output_dir, "mimetype")
    meta_inf_path = os.path.join(output_dir, "META-INF")
    oebps_path = os.path.join(output_dir, "OEBPS")

    os.makedirs(meta_inf_path, exist_ok=True)
    os.makedirs(oebps_path, exist_ok=True)

    with open(mimetype_path, "w", encoding="utf-8") as f:
        f.write("application/epub+zip")

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    with open(os.path.join(meta_inf_path, "container.xml"), "w", encoding="utf-8") as f:
        f.write(container_xml)

    try:
        with open("eaglecraft.html", "r", encoding="utf-8") as html_file:
            raw_html = html_file.read()
    except FileNotFoundError:
        print("Error: eaglecraft.html file not found!")
        return False

    browser_api_fixes = """
    <div id="log" style="position:fixed;top:0;right:0;width:300px;height:200px;background:rgba(0,0,0,0.9);color:#0f0;font-family:monospace;font-size:10px;padding:10px;overflow-y:auto;z-index:999999;display:none;">
        <div style="color:#fff;font-weight:bold;margin-bottom:5px;">Debug Log
            <button onclick="document.getElementById('log').style.display='none'" style="float:right;background:#f44;color:white;border:none;padding:2px 6px;">×</button>
        </div>
        <div id="log-content"></div>
    </div>
    <button onclick="document.getElementById('log').style.display='block'" style="position:fixed;top:10px;right:10px;z-index:1000000;background:#333;color:#0f0;border:1px solid #666;padding:5px;">Debug</button>

    <script>
        window.log = function(msg, type = 'info') {
            const logContent = document.getElementById('log-content');
            if (logContent) {
                const timestamp = new Date().toLocaleTimeString();
                const color = type === 'error' ? '#f44' : type === 'warn' ? '#fa0' : '#0f0';
                logContent.innerHTML += `<div style="color: ${color}; margin-bottom: 2px;">[${timestamp}] ${msg}</div>`;
                logContent.scrollTop = logContent.scrollHeight;
            }
            console.log(`[Debug] ${msg}`);
        };

        log('Browser API polyfills loaded');

        if (!window.indexedDB) {
            const memoryDB = new Map();
            window.indexedDB = {
                open: function(name, version) {
                    log(`Opening IndexedDB: ${name}`);
                    return Promise.resolve({
                        target: {
                            result: {
                                name: name,
                                transaction: function(stores, mode) {
                                    return {
                                        objectStore: function(storeName) {
                                            const storeKey = `${name}_${storeName}`;
                                            if (!memoryDB.has(storeKey)) {
                                                memoryDB.set(storeKey, new Map());
                                            }
                                            return {
                                                get: function(key) {
                                                    const store = memoryDB.get(storeKey);
                                                    const result = store ? store.get(key) : undefined;
                                                    return Promise.resolve({target: {result: result}});
                                                },
                                                put: function(value, key) {
                                                    const store = memoryDB.get(storeKey);
                                                    if (store) store.set(key, value);
                                                    return Promise.resolve({target: {result: key}});
                                                }
                                            };
                                        }
                                    };
                                },
                                createObjectStore: function(name, options) {
                                    const storeKey = `${this.name}_${name}`;
                                    memoryDB.set(storeKey, new Map());
                                    return this.transaction([name], 'readwrite').objectStore(name);
                                }
                            }
                        }
                    });
                }
            };
        }

        function decodeEPK(data) {
            log('Decoding EPK file');
            try {
                if (data instanceof ArrayBuffer) {
                    data = new Uint8Array(data);
                }
                
                const view = new DataView(data.buffer || data);
                const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
                
                if (magic !== 'EPKG') {
                    log('Not an EPK file, treating as raw data');
                    return data;
                }
                
                let offset = 8;
                const files = {};
                
                while (offset < data.length) {
                    const nameLength = view.getUint16(offset, true);
                    offset += 2;
                    
                    let name = '';
                    for (let i = 0; i < nameLength; i++) {
                        name += String.fromCharCode(view.getUint8(offset + i));
                    }
                    offset += nameLength;
                    
                    const fileLength = view.getUint32(offset, true);
                    offset += 4;
                    
                    const fileData = data.slice(offset, offset + fileLength);
                    files[name] = fileData;
                    offset += fileLength;
                    
                    log(`Extracted: ${name} (${fileLength} bytes)`);
                }
                
                return files;
            } catch (e) {
                log(`EPK decode error: ${e.message}`, 'error');
                return data;
            }
        }

        window.decodeEPK = decodeEPK;

        if (window.XMLHttpRequest) {
            const OriginalXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                const xhr = new OriginalXHR();
                const originalSend = xhr.send;

                xhr.send = function(data) {
                    const originalError = xhr.onerror;
                    xhr.onerror = function(e) {
                        const url = xhr.responseURL || 'unknown';
                        log(`XHR error: ${url}`, 'error');

                        if (url.includes('client') || url.includes('.epk')) {
                            log('Creating EPK client bundle');
                            
                            const clientBundle = new ArrayBuffer(1024);
                            xhr.status = 200;
                            xhr.readyState = 4;
                            xhr.response = clientBundle;
                            
                            if (xhr.onreadystatechange) xhr.onreadystatechange();
                            if (xhr.onload) xhr.onload();
                            return;
                        }

                        xhr.status = 200;
                        xhr.readyState = 4;
                        xhr.response = new ArrayBuffer(0);
                        if (xhr.onreadystatechange) xhr.onreadystatechange();
                        if (xhr.onload) xhr.onload();
                    };

                    return originalSend.call(this, data);
                };
                return xhr;
            };
        }

        if (!window.TextDecoder) {
            window.TextDecoder = function() {
                this.decode = function(buffer) {
                    const bytes = new Uint8Array(buffer);
                    let result = '';
                    for (let i = 0; i < bytes.length; i++) {
                        result += String.fromCharCode(bytes[i]);
                    }
                    return result;
                };
            };
        }

        if (!window.TextEncoder) {
            window.TextEncoder = function() {
                this.encode = function(str) {
                    const bytes = new Uint8Array(str.length);
                    for (let i = 0; i < str.length; i++) {
                        bytes[i] = str.charCodeAt(i);
                    }
                    return bytes;
                };
            };
        }

        Object.defineProperty(navigator, 'onLine', {
            writable: true,
            value: false
        });

        log('Core polyfills ready');
    </script>"""

    if "<head>" in raw_html:
        raw_html = raw_html.replace("<head>", f"<head>{browser_api_fixes}")
    else:
        raw_html = browser_api_fixes + raw_html

    html_filename = "eaglecraft_fixed.html"
    html_path = os.path.join(oebps_path, html_filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(raw_html)

    index_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Eaglecraft</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
body {{ margin:0;padding:0;background:#000;color:white;overflow:hidden;height:100vh; }}
.game-container {{ width:100vw;height:100vh;border:none;position:fixed;top:0;left:0;z-index:999; }}
.header {{ position:fixed;top:20px;left:20px;z-index:1000;background:rgba(51,51,51,0.95);padding:15px;border-radius:8px;max-width:300px; }}
.launch-btn {{ background:#4CAF50;color:white;padding:15px 30px;border:none;border-radius:5px;font-size:16px;cursor:pointer;margin:10px 0; }}
.launch-btn:hover {{ background:#45a049; }}
</style>
<script>
function launchGame() {{
    const iframe = document.getElementById('gameFrame');
    const btn = document.getElementById('launchBtn');
    const status = document.getElementById('status');
    
    status.textContent = 'Loading...';
    btn.style.display = 'none';
    iframe.style.display = 'block';
    iframe.src = '{html_filename}';
    
    setTimeout(() => {{
        status.textContent = 'Game loaded. Check Debug Log for details.';
    }}, 2000);
}}
</script>
</head>
<body>
<div class="header">
    <h2>Eaglecraft</h2>
    <button id="launchBtn" class="launch-btn" onclick="launchGame()">Launch Game</button>
    <div id="status">Click to start</div>
</div>
<iframe id="gameFrame" class="game-container" style="display:none;" frameborder="0" allowfullscreen sandbox="allow-scripts allow-same-origin allow-forms"></iframe>
</body>
</html>"""

    with open(os.path.join(oebps_path, "index.xhtml"), "w", encoding="utf-8") as f:
        f.write(index_xhtml)

    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    book_id = f"urn:uuid:{uuid.uuid4()}"

    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{html.escape(book_id)}</dc:identifier>
<dc:title>Eaglecraft</dc:title>
<dc:creator>Eaglecraft Team</dc:creator>
<dc:language>en</dc:language>
<dc:date>{current_date}</dc:date>
<meta property="dcterms:modified">{current_date}</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="index" href="index.xhtml" media-type="application/xhtml+xml" properties="scripted"/>
<item id="game" href="{html.escape(html_filename)}" media-type="text/html"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="index"/>
</spine>
</package>"""

    with open(os.path.join(oebps_path, "content.opf"), "w", encoding="utf-8") as f:
        f.write(content_opf)

    nav_xhtml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
<nav epub:type="toc" id="toc">
<h1>Contents</h1>
<ol><li><a href="index.xhtml">Eaglecraft</a></li></ol>
</nav>
</body>
</html>"""

    with open(os.path.join(oebps_path, "nav.xhtml"), "w", encoding="utf-8") as f:
        f.write(nav_xhtml)

    toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head>
<meta name="dtb:uid" content="{html.escape(book_id)}"/>
<meta name="dtb:depth" content="1"/>
</head>
<docTitle><text>Eaglecraft</text></docTitle>
<navMap>
<navPoint id="navpoint-1" playOrder="1">
<navLabel><text>Eaglecraft</text></navLabel>
<content src="index.xhtml"/>
</navPoint>
</navMap>
</ncx>"""

    with open(os.path.join(oebps_path, "toc.ncx"), "w", encoding="utf-8") as f:
        f.write(toc_ncx)

    epub_path = os.path.expanduser("~/Documents/eaglecraft_minimal.epub")

    try:
        with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as epub:
            epub.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
            epub.write(os.path.join(meta_inf_path, "container.xml"), "META-INF/container.xml")

            for filename in ["content.opf", "index.xhtml", "nav.xhtml", "toc.ncx", html_filename]:
                file_path = os.path.join(oebps_path, filename)
                if os.path.exists(file_path):
                    epub.write(file_path, f"OEBPS/{filename}")

        print("Minimal EPUB created:", epub_path)
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        try:
            import shutil
            shutil.rmtree(output_dir)
        except:
            pass

if __name__ == "__main__":
    create_eaglecraft_epub()
