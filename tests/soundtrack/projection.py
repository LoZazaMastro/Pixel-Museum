import copy, runpy
m=runpy.run_path('tools/runtime-catalog.py')
cue={'youtube_id':'AAAAAAAAAAA','title':'Cue','source_page':'https://example.org/chapters','start_seconds':2.125,'end_seconds':15.75,'research_receipt':'discard'}
c={'entries':[{'id':'x','soundtrack':{'tracks':[cue]},'soundtrack_rooms':[{'title':'One','tracks':[cue]},{'title':'Two','tracks':[dict(cue,start_seconds=18,end_seconds=25)]}]}]}
before=copy.deepcopy(c);r=m['project'](c)['entries'][0]
assert c==before
assert len(r['soundtrack_rooms'])==2
for t in [r['soundtrack']['tracks'][0],*[x['tracks'][0] for x in r['soundtrack_rooms']]]:
 assert 'start_seconds' in t and 'end_seconds' in t and 'research_receipt' not in t
assert r['soundtrack_rooms'][0]['tracks'][0]['start_seconds']==2.125
assert r['soundtrack_rooms'][1]['tracks'][0]['start_seconds']==18
print('Runtime projection PASS: immutable authoring, exact cue bounds and independent rooms retained.')
