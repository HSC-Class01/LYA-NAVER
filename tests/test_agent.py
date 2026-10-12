import unittest
import agent
class TestAgent(unittest.TestCase):
 def test_num(self):
  self.assertEqual(agent.num('(1,234)'),-1234)
  self.assertIsNone(agent.num('-'))
  self.assertIsNone(agent.ratio(4,0))
  self.assertIsNone(agent.ratio(4,-1))
 def test_cumulative(self):
  rows=[{'sj_div':'IS','account_id':'ifrs-full_Revenue','thstrm_amount':'20','thstrm_add_amount':'60','currency':'KRW'}]
  v,_,_=agent.extract(rows,9); self.assertEqual(v['revenue'],60)
  rows[0]['thstrm_add_amount']=''; v,_,_=agent.extract(rows,9); self.assertIsNone(v['revenue'])
  v,_,_=agent.extract(rows,3); self.assertEqual(v['revenue'],20)
 def test_ambiguous(self):
  rows=[{'sj_div':'BS','account_id':'ifrs-full_Assets','thstrm_amount':str(n)} for n in [10,20]]
  self.assertIsNone(agent.extract(rows,12)[0]['assets'])
 def test_average_roe(self):
  rs=[{'year':2020,'month':12,'basis':'CFS','values':{'equity':100,'assets':200,'revenue':100,'net_income':10}}, {'year':2021,'month':12,'basis':'CFS','values':{'equity':120,'assets':240,'revenue':120,'net_income':11}}]
  out=agent.analyze(rs); self.assertEqual(out[1]['values']['roe'],10); self.assertEqual(out[1]['values']['roa'],5); self.assertEqual(out[1]['values']['revenue_yoy'],20)
 def test_scope_separation(self):
  rs=[{'year':2020,'month':12,'basis':'OFS','values':{'equity':100}}, {'year':2021,'month':12,'basis':'CFS','values':{'equity':120,'net_income':11}}]
  self.assertIsNone(agent.analyze(rs)[1]['values']['roe'])
 def test_period(self):
  self.assertEqual(agent.period({'report_nm':'[기재정정]사업보고서 (2010.12)'}),(2010,12))
if __name__=='__main__': unittest.main()
