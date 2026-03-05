import { describe, expect, it } from "vitest";

describe("jsdom regression coverage", () => {
  it("applies CSS specificity and !important correctly in computed styles", () => {
    const style = document.createElement("style");
    style.textContent = `
      #target { color: rgb(0, 128, 0); }
      .target { color: rgb(255, 0, 0) !important; }
      div { color: rgb(0, 0, 255); }
    `;
    document.head.appendChild(style);

    const el = document.createElement("div");
    el.id = "target";
    el.className = "target";
    document.body.appendChild(el);

    const computed = window.getComputedStyle(el);
    expect(computed.color).toBe("rgb(255, 0, 0)");

    el.remove();
    style.remove();
  });

  it("returns the first element in tree order when duplicate IDs exist", () => {
    const root = document.createElement("div");
    root.innerHTML = `
      <section id="duplicate-id">first</section>
      <section id="duplicate-id">second</section>
    `;
    document.body.appendChild(root);

    const first = root.children[0];
    const selected = document.getElementById("duplicate-id");

    expect(selected).toBe(first);

    root.remove();
  });

  it("updates FileReader result and events in expected order", async () => {
    const reader = new FileReader();
    const events: string[] = [];

    const done = new Promise<void>((resolve, reject) => {
      reader.addEventListener("loadstart", () => events.push("loadstart"));
      reader.addEventListener("load", () => events.push("load"));
      reader.addEventListener("loadend", () => {
        events.push("loadend");
        resolve();
      });
      reader.addEventListener("error", () => reject(reader.error ?? new Error("file read failed")));
    });

    const file = new File(["hello-jsdom"], "sample.txt", { type: "text/plain" });
    reader.readAsText(file);

    await done;
    expect(reader.result).toBe("hello-jsdom");
    expect(events).toEqual(["loadstart", "load", "loadend"]);
  });
});
