"""Publish reproducible ADM screening inputs from canonical evidence. No ownership imputation."""
import csv,json
from pathlib import Path
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
root=parser.parse_args().root.resolve()
def rows(p):
 with (root/p).open() as f:return list(csv.DictReader(f))
all_public=rows('data/processed/public_project_exposure_alberta.csv')
infra=[r for r in all_public if r['developer']=='Alberta Infrastructure']
exposed=[r for r in infra if r['schedule_overlap_status']=='overlaps']
fields=['project_id','name','municipality','stage','start_year','end_year','asset_class','developer','as_of_date']
power=[r for r in rows('data/processed/alberta_ai_projects.csv') if r['ai_relevance']=='enabling_power']
data={'version':1,'inventoryAsOf':max(r['as_of_date'] for r in infra),'scope':'Developer exactly equals Alberta Infrastructure; legal ownership and current package phase are unverified.','infrastructureCount':len(infra),'missingScheduleCount':sum(r['schedule_overlap_status']=='indeterminate_incomplete_schedule' for r in infra),'exposure':[ {k:r[k] for k in fields} for r in exposed],'power':[{'name':r['name'],'region':r['municipality'],'cost':float(r['estimated_cost_cad']),'mw':float(r['power_generation_capacity_mw']),'end':int(r['end_year']),'stage':r['stage'],'source':r['project_website']} for r in power],'powerContext':{'source':'https://www.aeso.ca/grid/connecting-to-the-grid/large-load-projects/','verifiedOn':'2026-09-06','phase1AllocatedMW':1200,'contracts':[{'name':'GLDC Load','mw':970},{'name':'Keephills Data Centre Phase I','mw':230}],'interpretation':'Executed load contracts proceed through connection studies. Phase 2A uses a BYOG process. No delay to a public facility is inferred.'}}
(root/'public/data/construction/adm-evidence.json').write_text(json.dumps(data,indent=2)+'\n')
print(f'Published {len(exposed)} Infrastructure developer overlap records; {len(power)} enabling-power records.')
