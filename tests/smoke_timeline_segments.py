"""Variable windows, per-seam overlap and zero-overlap boundary regression."""
import copy
from pathlib import Path
import sys
import json
from unittest.mock import patch
import torch
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_finite_segments import _load_package, _plan

finite = _load_package(Path(__file__).resolve().parents[1])

single=_plan()
single['segment_count']=0
single['timeline']['globalPrompt']='A material-free text-to-video prompt'
single['timeline']['videoClips']=[]
single['timeline']['images']=[]
single['timeline']['audios']=[]
single['timeline']['segmentConfig']={'count':0,'segments':[]}
single_plan=finite._require_finite_plan(single)
assert single_plan['mode']=='single_segment'
assert single_plan['prompts']==['A material-free text-to-video prompt']
assert single_plan['segment_lengths']==[192] and single_plan['segment_overlaps']==[0]
single_result=finite.MiniMaxH3FiniteSegmentSampler.execute(
    model='model',clip='clip',vae='vae',audio_vae='audio_vae',finite_plan=single,
    sampler='sampler',sigmas=torch.tensor([1.,.5,0.]),seed=7,continue_audio_latent=True,
)
single_nodes=list(single_result.expand.values())
single_encoders=[n for n in single_nodes if n['class_type']=='MiniMaxH3TimelineEncoder']
assert len(single_encoders)==1
assert single_encoders[0]['inputs']['prompt']=='A material-free text-to-video prompt'
assert single_encoders[0]['inputs']['plan']['timeline']['images']==[]

source = _plan()
source['timeline']['segmentConfig'] = {'mode':'timeline','count':3,'segments':[
    {'startFrame':0,'endFrame':56,'prompt':'First','images':['p2','p1'],'audios':['a1']},
    {'startFrame':34,'endFrame':107,'prompt':'Second','images':['p1'],'audios':[]},
    {'startFrame':107,'endFrame':146,'prompt':'Third','images':[],'audios':['a2']},
]}
p = finite._require_finite_plan(source)
assert p['segment_lengths'] == [56,73,39]
assert p['segment_overlaps'] == [0,22,0]
assert p['target_output_frames'] == 146
assert [a['id'] for a in p['segment_plans'][0]['timeline']['images']] == ['p2','p1']
assert p['segment_plans'][1]['timeline']['selection']['start'] == 34/24
assert p['prompts'] == ['First','Second','Third']

# Global prompt is reused only when every segment prompt is empty. As soon as
# one local prompt exists, all local prompts are required and the global value
# is deliberately ignored.
global_only=copy.deepcopy(source)
global_only['timeline']['globalPrompt']='One shared prompt'
for segment in global_only['timeline']['segmentConfig']['segments']:segment['prompt']=''
assert finite._require_finite_plan(global_only)['prompts']==['One shared prompt']*3
local_override=copy.deepcopy(global_only)
for index,segment in enumerate(local_override['timeline']['segmentConfig']['segments']):segment['prompt']=f'Local {index+1}'
assert finite._require_finite_plan(local_override)['prompts']==['Local 1','Local 2','Local 3']
partial=copy.deepcopy(global_only);partial['timeline']['segmentConfig']['segments'][0]['prompt']='Only one'
try:finite._require_finite_plan(partial)
except ValueError as error:assert 'every segment' in str(error)
else:raise AssertionError('partial segment prompt mode accepted')
director=sys.modules[finite.__package__+'.minimax_h3_timeline_director']
source['timeline']['segmentConfig']['activeIndex']=1
with patch.object(director,'_create_prompt_media_bundle',side_effect=lambda plan:plan):
    selected,bundle,complete=director.MiniMaxH3TimelinePlanner.execute(
        640,352,8,json.dumps(source['timeline']),
    )
    assert selected['prompt_index']==2 and bundle['prompt_index']==2
    assert selected['length']==73 and selected['generation_seconds']==73/24
    assert [a['id'] for a in selected['timeline']['images']]==['p1']
    assert complete['prompt_index'] is None
    assert finite._require_finite_plan(complete)['segment_lengths']==[56,73,39]
# Source clips stay on their global clock and expose only this window's intersection.
source['timeline']['videoClips']=[{'id':'v','file':'clip.mp4','start':1.,'trimStart':4.,'duration':10.,'hasAudio':False,'referenceMode':'edit'}]
video_plan=finite._require_finite_plan(source)['segment_plans'][1]
spec=director._video_reference_specs(video_plan['timeline'])[0]
assert abs(spec['source_start']-(4+34/24-1))<1e-6
assert abs(spec['duration']-73/24)<1e-6
for field,value in [('startFrame',108),('prompt',''),('endFrame',145)]:
    bad=copy.deepcopy(source);bad['timeline']['segmentConfig']['segments'][2][field]=value
    try:finite._require_finite_plan(bad)
    except ValueError:pass
    else:raise AssertionError(f'Invalid {field} accepted')

result=finite.MiniMaxH3FiniteSegmentSampler.execute(
    model='model',clip='clip',vae='vae',audio_vae='audio_vae',finite_plan=source,
    sampler='sampler',sigmas=torch.tensor([1.,.5,0.]),seed=7,continue_audio_latent=True,
)
graph=result.expand
nodes=list(graph.values())
continuations=[n['inputs'] for n in nodes if n['class_type']=='MiniMaxH3FiniteLatentContinuation']
assert [n['overlap_frames'] for n in continuations]==[0,22,0]
assert 'previous_images' not in continuations[2] and 'previous_latent' not in continuations[2]
assert len([n for n in nodes if n['class_type']=='MiniMaxH3FiniteAudioTrimTail'])==1
assert [n['inputs']['plan']['length'] for n in nodes if n['class_type']=='MiniMaxH3TimelineEncoder']==[56,73,39]

# A locked soundtrack is sliced by each absolute GEN window, encoded into the
# target AV latent after video continuation, and bypasses Soft AV assembly.
locked=copy.deepcopy(source)
locked_audio={'id':'master','file':'master.flac','name':'master.flac','duration':30.,'trimStart':0.,'audioMode':'locked'}
locked['timeline']['audios']=[locked_audio]
for segment in locked['timeline']['segmentConfig']['segments']:segment['audios']=['master']
locked_result=finite.MiniMaxH3FiniteSegmentSampler.execute(
    model='model',clip='clip',vae='vae',audio_vae='audio_vae',finite_plan=locked,
    sampler='sampler',sigmas=torch.tensor([1.,.5,0.]),seed=7,continue_audio_latent=True,
)
locked_nodes=list(locked_result.expand.values())
assert len([n for n in locked_nodes if n['class_type']=='MiniMaxH3LockedAudioSlice'])==3
assert len([n for n in locked_nodes if n['class_type']=='VAEEncodeAudio'])==3
assert len([n for n in locked_nodes if n['class_type']=='MiniMaxH3LockAudioLatent'])==3
assert len([n for n in locked_nodes if n['class_type']=='MiniMaxH3LockedAudioMaster'])==1
assert not [n for n in locked_nodes if n['class_type']=='MiniMaxH3FiniteAudioTrimTail']
assert all(
    n['inputs']['continue_audio_latent'] is False
    for n in locked_nodes if n['class_type']=='MiniMaxH3FiniteLatentContinuation'
)
assert 'source soundtrack is encoded into every segment' in locked_result[3].lower()

# Locked audio is decoded once as full PCM, then sample-sliced.  A compressed
# source may be shorter than its metadata and a GEN range may extend past its
# end; both cases pad only the sampling interval instead of rejecting the job.
locked_slice_plan=copy.deepcopy(locked)
locked_slice_plan['timeline']['segmentConfig']={'count':0,'segments':[]}
locked_slice_plan['timeline']['selection']={'start':0.,'duration':56/24}
locked_slice_plan['length']=56
one_second_pcm={
    'sample_rate':1000,
    'waveform':torch.arange(1000,dtype=torch.float32).reshape(1,1,1000),
}
with patch.object(finite,'_locked_audio_pcm',return_value=one_second_pcm):
    padded=finite._locked_audio_interval(locked_slice_plan)
assert padded['waveform'].shape[-1]==round(56/24*1000)
assert torch.equal(padded['waveform'][...,:1000],one_second_pcm['waveform'])
assert torch.count_nonzero(padded['waveform'][...,1000:])==0
locked_slice_plan['timeline']['selection']={'start':.25,'duration':5/24}
locked_slice_plan['length']=5
with patch.object(finite,'_locked_audio_pcm',return_value=one_second_pcm):
    sliced=finite._locked_audio_interval(locked_slice_plan)
expected_samples=round(5/24*1000)
assert torch.equal(
    sliced['waveform'], one_second_pcm['waveform'][...,250:250+expected_samples],
)

from comfy.nested_tensor import NestedTensor
target={'samples':NestedTensor((torch.zeros(1,24,7,2,2),torch.zeros(1,32,2,12)))}
encoded={'samples':torch.ones(1,32,2,14)}
locked_latent=finite.MiniMaxH3LockAudioLatent.execute(target,encoded)[0]
video_stream,audio_stream=locked_latent['samples'].unbind()
video_mask,audio_mask=locked_latent['noise_mask'].unbind()
assert audio_stream.shape[-1]==12 and torch.all(audio_stream==1)
assert torch.all(video_mask==1) and torch.all(audio_mask==0)
images=torch.zeros(39,2,2,3);audio={'sample_rate':24000,'waveform':torch.ones(1,1,39000)}
out=finite.MiniMaxH3FiniteSegmentFinalize.execute({},images,2,3,0,True,audio)
assert out[1].shape[0]==39 and out[2]['waveform'].shape[-1]==39000
previous=torch.rand(73,2,2,3)
with patch.object(finite,'_apply_h3_guides',return_value='anchored') as guide:
    out=finite.MiniMaxH3FiniteLatentContinuation.execute('positive',{},2,3,0,True,'model',None,{},previous,'vae','audio_vae')
    assert out[0]=='positive' and out[2]==0 and out[3]=='model'
    guide.assert_not_called()
print('timeline segment planning and execution graph: PASS')
