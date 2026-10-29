// Runs Idea X-ray (Python) in the browser with Pyodide, off the main thread so the page stays responsive.
const LOCAL = ["localhost", "127.0.0.1"].includes(self.location.hostname);
const PYODIDE = LOCAL ? "./pyodide/" : "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
importScripts(PYODIDE + "pyodide.js");

const status = (text) => postMessage({ type: "status", text });

const ready = (async () => {
  status("Loading the X-ray engine (first time only, about 10 MB)…");
  const py = await loadPyodide({ indexURL: PYODIDE });
  const wheels = await (await fetch("py/manifest.json")).json();
  for (const name of wheels) {
    py.unpackArchive(await (await fetch("py/" + name)).arrayBuffer(), "wheel");
  }
  py.runPython("import idea_xray.browser as xray_browser");
  postMessage({ type: "ready" });
  return py;
})();
ready.catch((e) => postMessage({ type: "error", text: "The X-ray engine didn't load: " + e.message }));

onmessage = async (e) => {
  let py;
  try {
    py = await ready;
  } catch {
    return;
  }
  status("Searching Hacker News, GitHub, the App Store, Reddit and YC. This takes up to a minute…");
  try {
    py.globals.set("form_json", JSON.stringify(e.data));
    postMessage({ type: "result", data: JSON.parse(py.runPython("xray_browser.run(form_json)")) });
  } catch (err) {
    postMessage({ type: "error", text: "Something went wrong: " + String(err.message || err).split("\n").slice(-2).join(" ") });
  }
};
