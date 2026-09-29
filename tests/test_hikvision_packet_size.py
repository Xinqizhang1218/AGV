import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from agv_vision.core.exceptions import SourceError
from agv_vision.core.hikvision_source import HikvisionColorSource


class PacketSizeTests(unittest.TestCase):
    def make_source(self, use_ex=True, readback=1500, write_code=0, read_code=0):
        source = HikvisionColorSource(2448, 2048, 15)
        source.sdk = SimpleNamespace(MV_GIGE_DEVICE=1)
        value_type = "MVCC_INTVALUE_EX" if use_ex else "MVCC_INTVALUE"
        setattr(source.sdk, value_type, lambda: SimpleNamespace(nCurValue=0))
        suffix = "Ex" if use_ex else ""
        setter = Mock(return_value=write_code)

        def read_value(key, value):
            value.nCurValue = readback
            return read_code

        getter = Mock(side_effect=read_value)
        source.camera = SimpleNamespace(**{
            "MV_CC_SetIntValue" + suffix: setter,
            "MV_CC_GetIntValue" + suffix: getter,
        })
        return source, setter, getter

    def test_set_and_verify_both_sdk_versions(self):
        for use_ex in (True, False):
            with self.subTest(use_ex=use_ex):
                source, setter, getter = self.make_source(use_ex)
                source._configure_gige_packet_size(1)
                setter.assert_called_once_with("GevSCPSPacketSize", 1500)
                self.assertEqual(getter.call_args.args[0], "GevSCPSPacketSize")

    def test_usb_does_not_write_network_nodes(self):
        source, setter, getter = self.make_source()
        source._configure_gige_packet_size(4)
        setter.assert_not_called()
        getter.assert_not_called()

    def test_write_failure_stops_before_readback(self):
        source, _, getter = self.make_source(write_code=0x80000004)
        with self.assertRaises(SourceError):
            source._configure_gige_packet_size(1)
        getter.assert_not_called()

    def test_read_failure_is_not_ignored(self):
        source, _, _ = self.make_source(read_code=0x80000004)
        with self.assertRaises(SourceError):
            source._configure_gige_packet_size(1)

    def test_old_jumbo_value_is_rejected(self):
        source, _, _ = self.make_source(readback=8164)
        with self.assertRaisesRegex(SourceError, "8164"):
            source._configure_gige_packet_size(1)


if __name__ == "__main__":
    unittest.main()
