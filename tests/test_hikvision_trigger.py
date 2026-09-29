import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from agv_vision.core.exceptions import SourceError
from agv_vision.core.hikvision_source import HikvisionColorSource


class HikvisionTriggerTests(unittest.TestCase):
    def make_source(self, options):
        source = HikvisionColorSource(640, 480, 10)
        source.sdk = SimpleNamespace(
            MVCC_ENUMVALUE=lambda: SimpleNamespace(nSupportValue=[0] * 64),
            MVCC_ENUMENTRY=lambda: SimpleNamespace(nValue=0, chSymbolic=b""),
            MVCC_INTVALUE=lambda: SimpleNamespace(nCurValue=0),
        )
        state = {"TriggerSelector": next(iter(options)), "AcquisitionBurstFrameCount": 8}

        def read_enum(key, value):
            value.nCurValue = state[key]
            value.nSupportedNum = len(options)
            value.nSupportValue[:len(options)] = list(options)
            return 0

        def read_name(key, entry):
            entry.chSymbolic = options[entry.nValue].encode("ascii")
            return 0

        def write_value(key, value):
            state[key] = value
            return 0

        def read_integer(key, value):
            value.nCurValue = state[key]
            return 0

        source.camera = Mock()
        source.camera.MV_CC_GetEnumValue.side_effect = read_enum
        source.camera.MV_CC_GetEnumEntrySymbolic.side_effect = read_name
        source.camera.MV_CC_SetEnumValue.side_effect = write_value
        source.camera.MV_CC_SetIntValue.side_effect = write_value
        source.camera.MV_CC_GetIntValue.side_effect = read_integer
        return source, state

    def test_burst_only_camera_sets_one_frame(self):
        source, state = self.make_source({6: "FrameBurstStart"})
        source._configure_software_trigger()
        self.assertEqual(state["AcquisitionBurstFrameCount"], 1)
        self.assertEqual(state["TriggerSelector"], 6)
        self.assertEqual(state["TriggerSource"], 7)
        self.assertEqual(state["TriggerMode"], 1)

    def test_prefers_frame_start(self):
        source, state = self.make_source({6: "FrameBurstStart", 0: "FrameStart"})
        source._configure_software_trigger()
        self.assertEqual(state["TriggerSelector"], 0)
        source.camera.MV_CC_SetIntValue.assert_not_called()

    def test_unknown_selector_rejected_before_writes(self):
        source, _ = self.make_source({9: "Other"})
        with self.assertRaises(SourceError):
            source._configure_software_trigger()
        source.camera.MV_CC_SetEnumValue.assert_not_called()

    def test_burst_write_failure_rejected(self):
        source, _ = self.make_source({6: "FrameBurstStart"})
        source.camera.MV_CC_SetIntValue.side_effect = None
        source.camera.MV_CC_SetIntValue.return_value = 0x80000004
        with self.assertRaisesRegex(SourceError, "80000004"):
            source._configure_software_trigger()

    def test_burst_readback_mismatch_rejected(self):
        source, _ = self.make_source({6: "FrameBurstStart"})
        source.camera.MV_CC_SetIntValue.side_effect = lambda key, value: 0
        with self.assertRaisesRegex(SourceError, "AcquisitionBurstFrameCount=8"):
            source._configure_software_trigger()

    def test_enum_readback_mismatch_rejected(self):
        source, _ = self.make_source({6: "FrameBurstStart", 0: "FrameStart"})
        source.camera.MV_CC_SetEnumValue.side_effect = lambda key, value: 0
        with self.assertRaisesRegex(SourceError, "TriggerSelector"):
            source._configure_software_trigger()

    def test_ex_integer_api_is_paired_with_ex_structure(self):
        source, state = self.make_source({6: "FrameBurstStart"})
        source.sdk.MVCC_INTVALUE_EX = lambda: SimpleNamespace(nCurValue=0, is_ex=True)
        source.camera.MV_CC_SetIntValueEx.side_effect = source.camera.MV_CC_SetIntValue.side_effect

        def read_ex(key, value):
            self.assertTrue(value.is_ex)
            value.nCurValue = state[key]
            return 0

        source.camera.MV_CC_GetIntValueEx.side_effect = read_ex
        source._configure_software_trigger()
        source.camera.MV_CC_GetIntValue.assert_not_called()
        source.camera.MV_CC_SetIntValue.assert_not_called()


if __name__ == "__main__":
    unittest.main()
