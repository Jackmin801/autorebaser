from __future__ import annotations

import json
from pathlib import Path
import shutil
import textwrap

from .util import read_json, write_json


def render_video(directory: Path):
    from manim import (Scene, Text, VGroup, RoundedRectangle, Arrow, FadeIn,
                       FadeOut, Write, Transform, tempconfig, UP, DOWN, LEFT, RIGHT)
    import av

    evidence = read_json(directory / "evidence.json")
    story = read_json(directory / "storyboard.json")
    ink, white, muted, lime, blue, purple = "#111F1A", "#EFF4E8", "#A5B6A6", "#D9F078", "#84C9C1", "#C3A9E5"

    def text(value, size=28, color=white, width=12):
        result = Text(value, font="Arial", font_size=size, color=color)
        if result.width > width:
            result.scale_to_fit_width(width)
        return result

    def card(label, value, color=lime, width=3.6):
        rect = RoundedRectangle(width=width, height=1.5, corner_radius=.14, stroke_color="#425649", fill_color="#203329", fill_opacity=1)
        label_obj = text(label, 16, muted, width-.4).move_to(rect).shift(UP*.4)
        value_obj = text(value, 31, color, width-.4).move_to(rect).shift(DOWN*.15)
        return VGroup(rect, label_obj, value_obj)

    def persisted(label):
        for check in evidence["checks"]:
            if check["label"] == label and check["kind"] == "persistence":
                for line in check["output"].splitlines():
                    try:
                        data = json.loads(line)
                    except ValueError:
                        continue
                    if "persisted_count" in data:
                        return data["persisted_count"]
        return None

    def patch_graphic():
        diff = (directory / "patches/repair.diff").read_text()
        removed = [line[1:].strip() for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
        added = [line[1:].strip() for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        if not removed or not added or len(removed) > 4 or len(added) > 4:
            return None
        before = VGroup(text("BEFORE / FEATURE ASSUMPTION", 15, muted),
                        text("\n".join(removed), 25, "#ECA18F", 11)).arrange(DOWN, buff=.2).shift(UP*.6)
        after = VGroup(text("AFTER / COMMITTED REPAIR", 15, muted),
                       text("\n".join(added), 25, lime, 11)).arrange(DOWN, buff=.2).shift(DOWN*.65)
        return VGroup(before, after)

    class Explanation(Scene):
        def construct(self):
            brand = text("AUTOREBASER   /   CHANGE EXPLAINED", 17, lime).to_corner(UP+LEFT, buff=.5)
            sha = text(evidence["candidate"][:8], 17, muted).to_corner(UP+RIGHT, buff=.5)
            self.add(brand, sha)
            opening = text("Keep the feature.\nUnderstand the change.", 53, white, 11)
            self.play(FadeIn(opening, shift=UP*.15), run_time=.8)
            self.wait(3.2)
            self.play(FadeOut(opening), run_time=.5)
            for index, scene in enumerate(story["scenes"]):
                eyebrow = text(f"0{index+1} / 04", 16, lime).move_to(UP*2.6)
                title = text(scene["title"], 35, white, 11.8).move_to(UP*1.95)
                caption = text("\n".join(textwrap.wrap(scene["caption"], 82)), 23, muted, 11.7).move_to(DOWN*2.1)
                refs = text("EVIDENCE  " + " · ".join(scene["evidence_ids"]), 12, muted, 11.8).move_to(DOWN*3.15)
                if index == 0:
                    a = card("UPSTREAM", "Main evolves", blue).shift(LEFT*2.3)
                    b = card("FEATURE", "Intent preserved", purple).shift(RIGHT*2.3)
                    graphic = VGroup(a, b, Arrow(a.get_right(), b.get_left(), color=lime, buff=.18))
                elif index == 1:
                    checks = evidence["checks"]
                    first = next(c for c in checks if c["label"] == "original" and c["kind"] == "suite")
                    middle = next((c for c in checks if c["label"] == "mechanical-control" and c["kind"] == "suite"),
                                  next(c for c in checks if c["label"] == "integration" and c["kind"] == "suite"))
                    a = card("ORIGINAL FEATURE", "PASS" if first["passed"] else "FAIL").shift(LEFT*2.3)
                    b = card("IMPORT-ONLY CONTROL" if middle["label"] == "mechanical-control" else "INTEGRATION",
                             "PASS" if middle["passed"] else "FAIL", lime if middle["passed"] else "#ECA18F").shift(RIGHT*2.3)
                    graphic = VGroup(a, b)
                elif index == 2 and persisted("mechanical-control") is not None and persisted("final") is not None:
                    a = card("CONTROL / PERSISTED ROWS", str(persisted("mechanical-control")), "#ECA18F").shift(LEFT*2.3)
                    b = card("REPAIR / PERSISTED ROWS", str(persisted("final"))).shift(RIGHT*2.3)
                    graphic = VGroup(a, b, Arrow(a.get_right(), b.get_left(), color=lime, buff=.2),
                                     text("Checked after the writing process exits", 19, muted).shift(DOWN*1.1))
                elif index == 2:
                    graphic = card("SOURCE ADAPTATION", "Review the patch", lime, width=6)
                else:
                    final = next(c for c in evidence["checks"] if c["id"] == "final-suite")
                    a = card("REQUIRED TESTS", f"{final['test_count']} passed" if final.get("test_count") is not None else "Passed").shift(LEFT*2.3)
                    b = card("COMMITTED CANDIDATE", evidence["candidate"][:8], blue).shift(RIGHT*2.3)
                    graphic = VGroup(a, b)
                group = VGroup(eyebrow, title, graphic, caption, refs)
                self.play(FadeIn(eyebrow), Write(title), run_time=.9)
                source_change = patch_graphic() if index == 2 else None
                if source_change is not None:
                    self.play(FadeIn(source_change), FadeIn(caption), FadeIn(refs), run_time=.8)
                    self.wait(5)
                    self.play(Transform(source_change, graphic), run_time=.7)
                    group.remove(graphic)
                    group.add(source_change)
                    self.wait(5)
                else:
                    self.play(FadeIn(graphic, shift=UP*.15), FadeIn(caption), FadeIn(refs), run_time=.8)
                    self.wait(10.7)
                self.play(FadeOut(group), run_time=.5)
            close = text("Ready for your review.", 44, lime)
            self.play(FadeIn(close), run_time=.5)
            self.wait(2)

    with tempconfig({"pixel_width": 1280, "pixel_height": 720, "frame_rate": 24,
                     "background_color": ink, "media_dir": str(directory / "media"),
                     "output_file": "explanation", "write_to_movie": True,
                     "disable_caching": True, "preview": False, "verbosity": "ERROR", "progress_bar": "none"}):
        scene = Explanation()
        scene.render()
        source = Path(scene.renderer.file_writer.movie_file_path)
        shutil.copyfile(source, directory / "video.mp4")
    # Decode the real file and extract representative QA frames with PyAV.
    container = av.open(str(directory / "video.mp4"))
    stream = container.streams.video[0]
    duration = float(stream.duration * stream.time_base) if stream.duration else 0
    times, exported = [2, 10, 24, 39, 53], []
    for frame in container.decode(video=0):
        timestamp = float(frame.time or 0)
        if times and timestamp >= times[0]:
            at = times.pop(0)
            path = directory / f"frame-{at:02d}.png"
            frame.to_image().save(path)
            exported.append(path.name)
        if not times:
            break
    container.close()
    if duration < 30 or not exported:
        raise RuntimeError("Rendered video failed decode/duration validation")
    shutil.copyfile(directory / exported[0], directory / "poster.png")
    write_json(directory / "video.json", {"duration": duration, "width": 1280, "height": 720,
                                          "frames": exported, "renderer": "Manim Community"})
