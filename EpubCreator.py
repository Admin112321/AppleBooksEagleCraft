import os
import zipfile
from base64 import b64encode
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
<container version="1.0"
    xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf"
        media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    with open(os.path.join(meta_inf_path, "container.xml"), "w", encoding="utf-8") as f:
        f.write(container_xml)

    try:
        with open("eaglecraft.html", "r", encoding="utf-8") as html_file:
            raw_html = html_file.read()
    except FileNotFoundError:
        print("Error: eaglecraft.html file not found!")
        print("Please ensure eaglecraft.html exists in the current directory.")
        return False
    except Exception as e:
        print(f"Error reading eaglecraft.html: {e}")
        return False

    browser_api_fixes = """
    <div id="apple-books-logger" style="
        position: fixed; 
        top: 0; 
        right: 0; 
        width: 300px; 
        height: 200px; 
        background: rgba(0,0,0,0.9); 
        color: #0f0; 
        font-family: monospace; 
        font-size: 10px; 
        padding: 10px; 
        overflow-y: auto; 
        z-index: 999999; 
        border: 2px solid #666; 
        display: none;
    ">
        <div style="color: #fff; font-weight: bold; margin-bottom: 5px;">
            Apple Books Debug Log
            <button onclick="toggleDebugLog()" 
                    style="float: right; background: #f44; color: white; border: none; padding: 2px 6px;">×</button>
        </div>
        <div id="log-content"></div>
    </div>
    <button id="debug-toggle-btn" onclick="toggleDebugLog()" 
            style="position: fixed; top: 10px; right: 10px; z-index: 1000000; background: #333; color: #0f0; border: 1px solid #666; padding: 5px;">
        Debug Log
    </button>

    <script type="text/javascript">
   
        (function() {
            'use strict';

            window.appleLog = function(message, type = 'info') {
                const logContent = document.getElementById('log-content');
                if (logContent) {
                    const timestamp = new Date().toLocaleTimeString();
                    const color = type === 'error' ? '#f44' : type === 'warn' ? '#fa0' : '#0f0';
                    logContent.innerHTML += `<div style="color: ${color}; margin-bottom: 2px;">[${timestamp}] ${message}</div>`;
                    logContent.scrollTop = logContent.scrollHeight;
                }

                if (window.console) {
                    console.log(`[Apple Books] ${message}`);
                }
            };
            appleLog('Apple Books API implementation loaded');

            if (!window.indexedDB) {
                appleLog('Implementing IndexedDB for Apple Books', 'warn');

                const memoryDB = new Map();

                window.indexedDB = {
                    open: function(name, version) {
                        appleLog(`Opening IndexedDB: ${name} v${version}`);

                        return new Promise((resolve) => {
                            const db = {
                                name: name,
                                version: version || 1,
                                transaction: function(stores, mode = 'readonly') {
                                    return {
                                        objectStore: function(storeName) {
                                            const storeKey = `${name}_${storeName}`;
                                            if (!memoryDB.has(storeKey)) {
                                                memoryDB.set(storeKey, new Map());
                                            }

                                            return {
                                                get: function(key) {
                                                    return new Promise((resolve) => {
                                                        const store = memoryDB.get(storeKey);
                                                        const result = store ? store.get(key) : undefined;
                                                        resolve(result ? { target: { result: result } } : { target: { result: undefined } });
                                                    });
                                                },
                                                put: function(value, key) {
                                                    return new Promise((resolve) => {
                                                        const store = memoryDB.get(storeKey);
                                                        if (store) {
                                                            store.set(key, value);
                                                        }
                                                        resolve({ target: { result: key } });
                                                    });
                                                },
                                                delete: function(key) {
                                                    return new Promise((resolve) => {
                                                        const store = memoryDB.get(storeKey);
                                                        if (store) {
                                                            store.delete(key);
                                                        }
                                                        resolve({ target: { result: undefined } });
                                                    });
                                                }
                                            };
                                        }
                                    };
                                },
                                createObjectStore: function(name, options) {
                                    const storeKey = `${this.name}_${name}`;
                                    memoryDB.set(storeKey, new Map());
                                    appleLog(`Created object store: ${name}`);
                                    return this.transaction([name], 'readwrite').objectStore(name);
                                }
                            };

                            setTimeout(() => {
                                resolve({
                                    target: { result: db },
                                    target: { result: db }
                                });
                            }, 10);
                        });
                    }
                };
            }

            if (!window.caches) {
                appleLog('Implementing Cache API for Apple Books', 'warn');

                const memoryCache = new Map();

                window.caches = {
                    open: function(cacheName) {
                        return Promise.resolve({
                            match: function(request) {
                                const url = typeof request === 'string' ? request : request.url;
                                const cached = memoryCache.get(url);
                                return Promise.resolve(cached || undefined);
                            },
                            put: function(request, response) {
                                const url = typeof request === 'string' ? request : request.url;
                                memoryCache.set(url, response);
                                appleLog(`Cached: ${url}`);
                                return Promise.resolve();
                            },
                            delete: function(request) {
                                const url = typeof request === 'string' ? request : request.url;
                                const deleted = memoryCache.delete(url);
                                return Promise.resolve(deleted);
                            }
                        });
                    }
                };
            }
            if (window.fetch) {
                const originalFetch = window.fetch;
                window.fetch = function(url, options = {}) {
    appleLog(`Fetch request: ${url}`);

    // Only add timeout for non-WebSocket and non-critical network requests
    const isWebSocket = url.includes('ws://') || url.includes('wss://');
    const isServerRequest = url.includes('api.') || url.includes('server') || url.includes(':') || url.includes('http') || url.includes('ws');
    if (isWebSocket || isServerRequest) {
        // Let server requests use default timeout
        return originalFetch(url, {
            ...options,
            mode: 'cors',
            cache: 'no-cache'  // Changed for server requests
        }).then(response => {
            appleLog(`Fetch response: ${url} - ${response.status}`);
            return response;
        }).catch(error => {
            appleLog(`Fetch failed: ${url} - ${error.message}`, 'error');
            throw error;  // Re-throw for proper error handling
        });
    }

    // Keep timeout only for asset requests
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Network timeout')), 15000);
    });

    const fetchPromise = originalFetch(url, {
        ...options,
        mode: 'cors',
        cache: 'default'
    }).then(response => {
        appleLog(`Fetch response: ${url} - ${response.status}`);
        return response;
    }).catch(error => {
        appleLog(`Fetch failed: ${url} - ${error.message}`, 'error');
        throw error;
    });

    return Promise.race([fetchPromise, timeoutPromise]);
};
            if (window.XMLHttpRequest) {
                const OriginalXHR = window.XMLHttpRequest;
                window.XMLHttpRequest = function() {
                    const xhr = new OriginalXHR();
                    const originalOpen = xhr.open;
                    const originalSend = xhr.send;

                    xhr.open = function(method, url, async = true, user, password) {
    appleLog(`XHR ${method}: ${url}`);
    xhr.timeout = 15000;
    xhr._url = url; // Store URL for error handler
    
    xhr.ontimeout = function() {
        appleLog(`XHR timeout: ${url}`, 'warn');
        xhr.status = 200;
        xhr.readyState = 4;
        xhr.response = new ArrayBuffer(0);
        xhr.responseText = '';
        if (xhr.onload) xhr.onload();
    };

    return originalOpen.call(this, method, url, async, user, password);
};

                    xhr.send = function(data) {
                        const originalError = xhr.onerror;
                        xhr.onerror = function(e) {
    const url = xhr.responseURL || xhr._url || 'unknown';
    appleLog(`XHR attempting: ${url}`, 'info'); // Changed from 'error'

    // Don't fake successful responses for network requests
    if (url.includes('ws://') || url.includes('wss://') || url.includes('api.') || url.includes('server') || url.includes(':')) {
        // Let real network requests fail naturally for proper error handling
        if (originalError) originalError.call(this, e);
        return;
    }

    // Only fake responses for local asset requests
    if (url.includes('Bundle') || url.includes('bundle') || url.includes('client') || url.includes('eaglercraftx') || url.includes('.epk')) {
        xhr.status = 200;
        xhr.readyState = 4;
        xhr.statusText = 'OK';
        
        const epkHeader = new Uint8Array([0x45, 0x50, 0x4B, 0x00]);
        const bundleSize = new Uint8Array(4);
        const bundleData = new Uint8Array(1024);
        
        const fullBundle = new Uint8Array(epkHeader.length + bundleSize.length + bundleData.length);
        fullBundle.set(epkHeader, 0);
        fullBundle.set(bundleSize, epkHeader.length);
        fullBundle.set(bundleData, epkHeader.length + bundleSize.length);
        
        xhr.response = fullBundle.buffer;
        xhr.responseText = '';
        appleLog(`EPK bundle created: ${fullBundle.length} bytes`);
        
        if (xhr.onreadystatechange) xhr.onreadystatechange();
        if (xhr.onload) xhr.onload();
    } else {
        // Let other requests fail naturally
        if (originalError) originalError.call(this, e);
    }
};
                        return originalSend.call(this, data);
                    };

                    return xhr;
                };
            }

            if (window.HTMLCanvasElement) {
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(contextType, options) {
                    if (contextType === 'webgl' || contextType === 'experimental-webgl') {
                        appleLog(`Creating WebGL context with Apple Books optimizations`);
                        const gl = originalGetContext.call(this, contextType, {
                            ...options,
                            antialias: false,
                            depth: true,
                            stencil: false,
                            preserveDrawingBuffer: true,
                            powerPreference: 'default'
                        });

                        if (gl) {
                            appleLog('WebGL context created successfully');
                        } else {
                            appleLog('WebGL context creation failed', 'error');
                        }

                        return gl;
                    }

                    return originalGetContext.call(this, contextType, options);
                };
            }

            Object.defineProperty(navigator, 'onLine', {
                writable: true,
                value: true //////////////////TOGGLE ON/OFF FOR ONLINE MODE
            });

const originalCreateElement = document.createElement;
document.createElement = function(tagName) {
    const element = originalCreateElement.call(this, tagName);

    if (tagName.toLowerCase() === 'style' || tagName.toLowerCase() === 'link') {
        appleLog(`Creating ${tagName} element with Apple Books compatibility`);

        element.onerror = function() {
            appleLog(`${tagName} loading failed - using fallback`, 'warn');

        };
    }

    return element;
};
            appleLog('Apple Books browser API implementation complete');

        })();
        
        window.toggleDebugLog = function toggleDebugLog() {
    const logger = document.getElementById('apple-books-logger');
    const button = document.getElementById('debug-toggle-btn');
    
    if (logger && button) {
        if (logger.style.display === 'none' || logger.style.display === '') {
            logger.style.display = 'block';
            button.textContent = 'Hide Log';
            button.style.backgroundColor = '#f44';
        } else {
            logger.style.display = 'none';
            button.textContent = 'Debug Log';
            button.style.backgroundColor = '#333';
        }
    }
}
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
   <style type="text/css">
     <![CDATA[
body {{
 margin: 0;
 padding: 0;
 font-family: Arial, sans-serif;
 background-color: 
 color: white;
 overflow: hidden;
 height: 100vh;
}}
.game-container {{
 width: 100vw;
 height: 100vh;
 border: none;
 background-color: 
 position: fixed;
 top: 0;
 left: 0;
 z-index: 999;
}}
.header {{
   position: fixed;
   top: 20px;
   left: 20px;
   z-index: 1000;
   background-color: rgba(51, 51, 51, 0.95);
   padding: 15px;
   border-radius: 12px;
   text-align: center;
   max-width: 300px;
   box-shadow: 0 8px 32px rgba(0,0,0,0.5);
   transition: all 0.3s ease;
}}

.header.minimized {{
   width: 120px;
   height: 40px;
   padding: 8px;
   overflow: hidden;
}}

.header.minimized .launch-btn,
.header.minimized .status,
.header.minimized .loading,
.header.minimized h1,
.header.minimized p {{
   display: none;
}}

.minimize-btn {{
   position: absolute;
   top: 5px;
   right: 8px;
   background: transparent;
   border: none;
   color: white;
   font-size: 16px;
   cursor: pointer;
   padding: 2px 6px;
}}
     .launch-btn {{
       background-color: 
       color: white;
       padding: 20px 40px;
       text-align: center;
       text-decoration: none;
       display: inline-block;
       font-size: 18px;
       font-weight: bold;
       margin: 10px;
       cursor: pointer;
       border: none;
       border-radius: 8px;
       transition: all 0.3s ease;
       box-shadow: 0 4px 8px rgba(0,0,0,0.3);
       min-width: 200px;
       position: relative;
       z-index: 1001;
     }}
     .launch-btn:hover {{
       background-color: 
       transform: translateY(-2px);
       box-shadow: 0 6px 12px rgba(0,0,0,0.4);
     }}
     .launch-btn:active {{
       transform: translateY(0);
       box-shadow: 0 2px 4px rgba(0,0,0,0.3);
     }}
     .launch-btn:focus {{
       outline: 3px solid 
       outline-offset: 2px;
     }}
     .status {{
       margin-top: 15px;
       font-size: 14px;
       color: 
     }}
     .loading {{
       display: none;
       margin-top: 20px;
     }}
     .spinner {{
       border: 4px solid 
       border-top: 4px solid 
       border-radius: 50%;
       width: 40px;
       height: 40px;
       animation: spin 2s linear infinite;
       margin: 0 auto;
     }}
     @keyframes spin {{
       0% {{ transform: rotate(0deg); }}
       100% {{ transform: rotate(360deg); }}
     }}
     ]]>
   </style>
   <script type="text/javascript">
     <![CDATA[
     let gameLoaded = false;

     function toggleHeader() {{
       const header = document.querySelector('.header');
       header.classList.toggle('minimized');
     }}

     function launchGame() {{
       if (!gameLoaded) {{
         const iframe = document.getElementById('gameFrame');
         const launchBtn = document.getElementById('launchBtn');
         const status = document.getElementById('status');
         const loading = document.getElementById('loading');

         loading.style.display = 'block';
         status.textContent = 'Loading with Apple Books browser API support...';
         launchBtn.disabled = true;
         launchBtn.textContent = 'Loading...';

         iframe.style.display = 'block';
         iframe.src = '{html_filename}';

         setTimeout(function() {{
           launchBtn.style.display = 'none';
           loading.style.display = 'none';
           status.textContent = 'Game loaded! Use the Debug Log button in the top-right to monitor loading progress.';
           gameLoaded = true;
         }}, 3000);

         iframe.onload = function() {{
           status.textContent = 'Game interface loaded. Check Debug Log for detailed loading progress.';
         }};

         iframe.onerror = function() {{
           status.textContent = 'Error loading game. Check Debug Log for details.';
           launchBtn.disabled = false;
           launchBtn.textContent = 'Retry Launch';
           launchBtn.style.display = 'inline-block';
           loading.style.display = 'none';
         }};
       }}
     }}

     document.addEventListener('DOMContentLoaded', function() {{
       const header = document.querySelector('.header');
       const minimizeBtn = document.createElement('button');
       minimizeBtn.className = 'minimize-btn';
       minimizeBtn.innerHTML = '−';
       minimizeBtn.onclick = toggleHeader;
       header.appendChild(minimizeBtn);

       const launchBtn = document.getElementById('launchBtn');
       if (launchBtn) {{
         launchBtn.addEventListener('click', launchGame);
       }}
     }});
     ]]>
   </script>
 </head>
 <body>
   <div class="header">
     <h1>Eaglecraft - Apple Books Enhanced</h1>
     <p>With comprehensive browser API support and visible debugging</p>
     <button id="launchBtn" class="launch-btn">Launch Game</button>
     <div id="loading" class="loading">
       <div class="spinner"></div>
       <p>Loading game with browser API support...</p>
     </div>
     <div id="status" class="status">Click the button above to start</div>
   </div>
   <iframe id="gameFrame" 
           class="game-container" 
           style="display: none;"
           frameborder="0" 
           allowfullscreen="true"
           sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads">
     <p>Your browser does not support embedded HTML games.</p>
   </iframe>
 </body>
</html>"""

    with open(os.path.join(oebps_path, "index.xhtml"), "w", encoding="utf-8") as f:
        f.write(index_xhtml)

    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    book_id = f"urn:uuid:{uuid.uuid4()}"

    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" 
         version="3.0" 
         unique-identifier="bookid">

  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{html.escape(book_id)}</dc:identifier>
    <dc:title>Eaglecraft - Apple Books</dc:title>
    <dc:creator>WereWolf</dc:creator>
    <dc:language>en</dc:language>
    <dc:subject>Games</dc:subject>
    <dc:description>Eaglecraft in apple books</dc:description>
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
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>Navigation</title>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>Table of Contents</h1>
      <ol>
        <li><a href="index.xhtml">Eaglecraft Game</a></li>
      </ol>
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
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>Eaglecraft - Apple Books</text>
  </docTitle>
  <navMap>
    <navPoint id="navpoint-1" playOrder="1">
      <navLabel>
        <text>Eaglecraft Game</text>
      </navLabel>
      <content src="index.xhtml"/>
    </navPoint>
  </navMap>
</ncx>"""

    with open(os.path.join(oebps_path, "toc.ncx"), "w", encoding="utf-8") as f:
        f.write(toc_ncx)

    epub_path = os.path.expanduser("~/Documents/eaglecraft_book.epub")

    try:
        with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as epub:
            epub.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
            epub.write(os.path.join(meta_inf_path, "container.xml"), "META-INF/container.xml")

            for filename in ["content.opf", "index.xhtml", "nav.xhtml", "toc.ncx", html_filename]:
                file_path = os.path.join(oebps_path, filename)
                if os.path.exists(file_path):
                    epub.write(file_path, f"OEBPS/{filename}")

        print("Apple Books EPUB created successfully:", epub_path)
        print(f"File size: {os.path.getsize(epub_path) / 1024 / 1024:.2f} MB")

        return True

    except Exception as e:
        print(f"Error creating EPUB: {e}")
        return False

    finally:
        try:
            import shutil
            shutil.rmtree(output_dir)
        except:
            pass

if __name__ == "__main__":

    if create_eaglecraft_epub():
        print("Use the 'Debug Log' button in-game to monitor loading progress")
    else:
        print('make sure eaglecraft.html is in the scope.')
