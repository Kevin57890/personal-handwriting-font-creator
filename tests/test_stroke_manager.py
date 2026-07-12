from __future__ import annotations

import unittest

from src.editor.stroke_manager import StrokeManager


class StrokeManagerTests(unittest.TestCase):
    def test_draw_undo_redo_transform_and_erase(self) -> None:
        manager = StrokeManager()
        manager.begin_stroke(10, 10, timestamp=1.0)
        manager.add_point(110, 10, timestamp=1.1)
        self.assertTrue(manager.end_stroke())
        self.assertEqual(len(manager.strokes), 1)

        manager.translate(20, 30)
        self.assertAlmostEqual(manager.strokes[0][0].x, 30)
        self.assertAlmostEqual(manager.strokes[0][0].y, 40)

        self.assertTrue(manager.undo())
        self.assertAlmostEqual(manager.strokes[0][0].x, 10)
        self.assertAlmostEqual(manager.strokes[0][0].y, 10)

        self.assertTrue(manager.redo())
        self.assertAlmostEqual(manager.strokes[0][0].x, 30)
        self.assertAlmostEqual(manager.strokes[0][0].y, 40)

        self.assertTrue(manager.erase_near(80, 40, 20))
        self.assertEqual(manager.strokes, [])

        self.assertTrue(manager.undo())
        self.assertEqual(len(manager.strokes), 1)

    def test_json_round_trip(self) -> None:
        manager = StrokeManager()
        manager.load_json_strokes([[[1, 2, 3, 0.5], [4, 5, 6, 0.7]]])
        self.assertEqual(manager.to_json_strokes(), [[[1.0, 2.0, 3.0, 0.5], [4.0, 5.0, 6.0, 0.7]]])

    def test_fit_to_rect_preserves_aspect_ratio_and_undo(self) -> None:
        manager = StrokeManager()
        manager.load_json_strokes([[[10, 20, 1, 1], [110, 70, 2, 1]]])

        self.assertTrue(manager.fit_to_rect(100, 120, 240, 160))
        min_x, min_y, max_x, max_y = manager.bounds() or (0, 0, 0, 0)
        self.assertAlmostEqual(min_x, 100)
        self.assertAlmostEqual(max_x, 340)
        self.assertAlmostEqual(max_y, 280)
        self.assertAlmostEqual(max_y - min_y, 120)

        self.assertTrue(manager.undo())
        self.assertEqual(manager.bounds(), (10.0, 20.0, 110.0, 70.0))


if __name__ == "__main__":
    unittest.main()
