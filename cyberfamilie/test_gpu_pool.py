import tempfile
import unittest
from pathlib import Path
from unittest import mock

import gpu_pool

class PoolTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"titel":"Test", "shots":[{"id":"a", "duur_seconden":4}, {"id":"b", "duur_seconden":4}]}
    def test_catalog_has_regions(self):
        regions = {x['region'] for x in gpu_pool.CATALOG}
        self.assertIn('China',regions)
        self.assertIn('India',regions)
        self.assertIn('Russia',regions)
    @mock.patch('gpu_pool.pipeline.clip_path',side_effect=lambda id: Path('/tmp/no-real-cyberfamilie-gpu-'+id+'.mp4'))
    def test_different_scenes_different_backends(self, clip_path):
        jobs = gpu_pool.planned_jobs(self.plan, ('wan','hunyuan'))
        self.assertEqual([x['provider'] for x in jobs],['wan','hunyuan'])
    def test_refuse_paid_backend(self):
        with self.assertRaises(ValueError):
            gpu_pool.planned_jobs(self.plan, ('alibaba_pai_dsw',))
    def test_refuse_absurd_parallelism(self):
        with self.assertRaises(ValueError):
            gpu_pool.render_parallel(self.plan, ('wan','hunyuan'), 200)
    def test_file_exists_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)/'a.mp4'
            target.write_bytes(b'invalid')
            with mock.patch('gpu_pool.pipeline.clip_path',return_value=target), mock.patch('gpu_pool.pipeline.call_public_provider') as remote:
                out = gpu_pool.attempt_free_render(self.plan['shots'][0], 'wan',self.plan)
                self.assertEqual(out['status'],'blocked_existing_clip')
                remote.assert_not_called()
                self.assertEqual(target.read_bytes(),b'invalid')

if __name__ == '__main__': unittest.main()