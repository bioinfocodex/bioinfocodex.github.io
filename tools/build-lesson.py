#!/usr/bin/env python3
"""Turn an OpenMAIC classroom export into a lesson the site can serve.

Why this exists: OpenMAIC plays lessons inside its own app, which needs a server
and a model behind it. The site is static files on Netlify. So each lesson is
unpacked into plain files under lesson-files/<slug>/ and the Lessons page in
index.html renders them: the video with a captions track, the outline, the
quiz, any interactive simulations, and the narration as a transcript.

Inputs come from OpenMAIC's export menu:
  - Export Classroom ZIP        -> the .maic.zip (scenes, quiz, narration, simulations)
  - Export Video -> Render MP4  -> the video (render it with burn-in subtitles OFF)
  - Export Video -> Download subtitles (.srt)

    python3 tools/build-lesson.py lesson.maic.zip --slug photosynthesis \\
        --video lesson.mp4 --srt lesson.srt \\
        --subject "Foundations" --summary "One or two sentences for the card."

    python3 tools/build-lesson.py --list      # show the catalogue, write nothing

Re-running with the same slug replaces that lesson. The catalogue,
lesson-files/index.json, is rebuilt from the lesson folders on every run.

If ffmpeg is on PATH the video is rewritten with +faststart (so it starts
playing before it has fully downloaded) and a poster frame is taken from it.
Without ffmpeg the video is copied as is and the page shows no poster.
"""
import argparse, json, pathlib, re, shutil, subprocess, sys, tempfile, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "lesson-files"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_manifest(zpath):
    with zipfile.ZipFile(zpath) as z:
        return json.loads(z.read("manifest.json"))


def narration(scene):
    return [a["text"].strip() for a in scene.get("actions", [])
            if a.get("type") == "speech" and a.get("text", "").strip()]


def vocabulary(manifest):
    words = set()
    for s in manifest["scenes"]:
        for line in narration(s):
            words.update(w.lower() for w in re.findall(r"[A-Za-z]+", line))
    return words


def mend(text, vocab):
    """Rejoin words OpenMAIC's subtitle splitter broke ("mecha nisms").

    Two neighbouring fragments are joined only when the joined word appears in
    the lesson's own narration and at least one fragment does not, so real
    word pairs are left alone.
    """
    tokens = text.split(" ")
    out = []
    for tok in tokens:
        if out:
            a, b = re.sub(r"\W", "", out[-1]).lower(), re.sub(r"\W", "", tok).lower()
            if a and b and (a + b) in vocab and (a not in vocab or b not in vocab):
                out[-1] = out[-1] + tok
                continue
        out.append(tok)
    return " ".join(out)


def srt_to_vtt(srt_text, vocab):
    lines = ["WEBVTT", ""]
    last_end = 0.0
    for block in re.split(r"\n\s*\n", srt_text.strip()):
        rows = block.strip().splitlines()
        if len(rows) < 3 or "-->" not in rows[1]:
            continue
        start, end = [t.strip().replace(",", ".") for t in rows[1].split("-->")]
        h, m, s = end.split(":")
        last_end = max(last_end, int(h) * 3600 + int(m) * 60 + float(s))
        lines += [f"{start} --> {end}", mend(" ".join(rows[2:]), vocab), ""]
    return "\n".join(lines), last_end


def quiz_questions(manifest):
    qs = []
    for s in manifest["scenes"]:
        if s["content"].get("type") != "quiz":
            continue
        for q in s["content"].get("questions", []):
            qs.append({
                "id": q["id"],
                "type": q["type"],                     # single | multiple | short_answer
                "question": q["question"],
                "options": q.get("options", []),
                "answer": q.get("answer", []),
                "explanation": q.get("analysis", ""),
                "points": q.get("points", 0),
            })
    return qs


def process_video(src, dest_dir):
    """Copy the video in; with ffmpeg, add +faststart and grab a poster."""
    video = dest_dir / "video.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        shutil.copyfile(src, video)
        return None
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(src), "-c", "copy",
                    "-movflags", "+faststart", str(video)], check=True)
    poster = dest_dir / "poster.jpg"
    subprocess.run([ffmpeg, "-v", "error", "-y", "-ss", "3", "-i", str(video),
                    "-frames:v", "1", "-q:v", "4", str(poster)], check=True)
    return poster.name


def build(args):
    if not SLUG_RE.match(args.slug):
        sys.exit(f"--slug must be lowercase words joined by hyphens, got {args.slug!r}")
    manifest = load_manifest(args.maic)
    vocab = vocabulary(manifest)
    dest = OUT / args.slug

    # Build into a scratch folder and swap it in, so a failure halfway never
    # leaves a half-written lesson behind for the site to serve.
    with tempfile.TemporaryDirectory(dir=OUT.parent) as tmp:
        work = pathlib.Path(tmp)
        scenes, sims = [], []
        for s in sorted(manifest["scenes"], key=lambda s: s.get("order", 0)):
            entry = {"title": s["title"], "type": s["type"], "narration": narration(s)}
            html = s["content"].get("html") if s["content"].get("type") == "interactive" else None
            if html:
                name = f"sim-{len(sims) + 1:02d}.html"
                (work / name).write_text(html, encoding="utf-8")
                sims.append({"title": s["title"], "file": name})
                entry["simulation"] = name
            scenes.append(entry)

        lesson = {
            "slug": args.slug,
            "title": manifest["stage"]["name"],
            "subject": args.subject,
            "summary": args.summary,
            "module": args.module,
            "scenes": scenes,
            "quiz": quiz_questions(manifest),
            "simulations": sims,
            "video": None, "poster": None, "captions": None, "duration": None,
            # Local builds report 0.0.0, which reads as a mistake on the page.
            "generator": " ".join(["OpenMAIC"] + [v for v in [manifest.get("appVersion")] if v and v != "0.0.0"]),
        }
        if args.video:
            lesson["poster"] = process_video(args.video, work)
            lesson["video"] = "video.mp4"
        if args.srt:
            vtt, seconds = srt_to_vtt(pathlib.Path(args.srt).read_text(encoding="utf-8"), vocab)
            (work / "captions.vtt").write_text(vtt, encoding="utf-8")
            lesson["captions"] = "captions.vtt"
            lesson["duration"] = round(seconds)

        (work / "lesson.json").write_text(json.dumps(lesson, indent=1, ensure_ascii=False), encoding="utf-8")
        if dest.exists():
            shutil.rmtree(dest)
        OUT.mkdir(exist_ok=True)
        shutil.move(str(work), dest)
        dest.chmod(0o755)   # mkdtemp makes it 0700
        work.mkdir()   # TemporaryDirectory expects its folder back to clean up

    write_catalogue()
    print(f"  lesson-files/{args.slug}/  ({len(scenes)} scenes, {len(lesson['quiz'])} questions, "
          f"{len(sims)} simulations)")


def catalogue():
    cards = []
    for f in sorted(OUT.glob("*/lesson.json")):
        l = json.loads(f.read_text(encoding="utf-8"))
        cards.append({k: l[k] for k in ("slug", "title", "subject", "summary", "module",
                                        "poster", "duration")}
                     | {"scenes": len(l["scenes"]), "questions": len(l["quiz"]),
                        "simulations": len(l["simulations"]), "video": bool(l["video"])})
    cards.sort(key=lambda c: (c["subject"] or "", c["title"]))
    return cards


def write_catalogue():
    (OUT / "index.json").write_text(json.dumps(catalogue(), indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("maic", nargs="?", help="OpenMAIC classroom export (.maic.zip)")
    p.add_argument("--slug", help="URL name: /lessons/<slug>")
    p.add_argument("--video", help="rendered MP4 (burn-in subtitles off)")
    p.add_argument("--srt", help="subtitles exported alongside the video")
    p.add_argument("--subject", default="General", help="grouping on the Lessons page")
    p.add_argument("--summary", default="", help="one or two sentences for the lesson card")
    p.add_argument("--module", default=None, help="related /learn/<module> slug, if any")
    p.add_argument("--list", action="store_true", help="print the catalogue and exit")
    args = p.parse_args()

    if args.list:
        for c in catalogue() if OUT.exists() else []:
            print(f"  /lessons/{c['slug']:<24} {c['title']}")
        return
    if not args.maic or not args.slug:
        p.error("a .maic.zip and --slug are required")
    build(args)


if __name__ == "__main__":
    main()
