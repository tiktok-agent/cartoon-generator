import unittest
import gpu_connection_check as m
class Tests(unittest.TestCase):
    def test_endpoint_visible(self):
        def reader(url):
            if '/api/spaces/' in url: return {'sdk':'gradio','host':'demo.hf.space','runtime':{'stage':'RUNNING'}},None
            return {'named_endpoints':{'/generate_video':{}}},None
        got=m.check(m.SPACE_CONFIG[0],reader)
        self.assertEqual(got['status'],'api_endpoint_visible')
        self.assertFalse(got['gpu_job_submitted'])
    def test_unreachable_not_misreported(self):
        got=m.check(m.SPACE_CONFIG[0],lambda url:(None,'DNS error'))
        self.assertEqual(got['status'],'connection_failed')
    def test_changed_endpoint(self):
        def reader(url):
            if '/api/spaces/' in url: return {'sdk':'gradio'},None
            return {'named_endpoints':{'/other':{}}},None
        self.assertEqual(m.check(m.SPACE_CONFIG[1],reader)['status'],'api_endpoint_changed')
    def test_untrusted_metadata_host(self):
        self.assertEqual(m.host_from_metadata({'host':'attacker.com/evil'},'demo/name'),'demo-name.hf.space')
if __name__=='__main__': unittest.main()
