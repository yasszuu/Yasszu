import json, sys
D = "../shorts/"; cfg = json.load(open("page.json"))
parts = [open(D + "head.html").read().replace("__TITLE__", cfg["title"]), open(D + "common_a.js").read().replace("__ZMAX__", str(cfg["zmax"])),
         open("spec_top.js").read(), open(D + "common_b.js").read().replace("__HELPERS__", open(D + "helpers.js").read()), open("spec_body.js").read(), "</script>\n</body>\n</html>\n"]
open("page.html", "w").write("\n".join(parts).replace("__TL__", open("timeline.json").read()))
