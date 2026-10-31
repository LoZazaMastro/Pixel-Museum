// Regression: libswscale SIMD must not overrun the owned packed RGBA allocation.
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/frame.h>
#include <libavutil/opt.h>
#include <libavutil/buffer.h>
#include <libswscale/swscale.h>
}
#include <cstdio>
#include <vector>
#include <algorithm>
int main(){for(auto wh:std::vector<std::pair<int,int>>{{360,412},{720,824},{944,1080},{358,412},{426,480},{854,480},{2,2},{18,18},{1920,1080},{1080,1080},{640,480},{1280,720}}){int w=wh.first,h=wh.second;AVFrame*s=av_frame_alloc();s->width=w;s->height=h;s->format=AV_PIX_FMT_YUV420P;if(av_frame_get_buffer(s,32)<0)return 1;for(int p=0;p<3;p++)for(int y=0;y<(p?h/2:h);y++)std::fill_n(s->data[p]+y*s->linesize[p],p?w/2:w,80+p*40);std::vector<unsigned char>out(w*h*4+AV_INPUT_BUFFER_PADDING_SIZE+1024,0xCD);SwsContext*c=sws_alloc_context();av_opt_set_int(c,"srcw",w,0);av_opt_set_int(c,"srch",h,0);av_opt_set_int(c,"src_format",s->format,0);av_opt_set_int(c,"dstw",w,0);av_opt_set_int(c,"dsth",h,0);av_opt_set_int(c,"dst_format",AV_PIX_FMT_RGBA,0);av_opt_set_int(c,"sws_flags",SWS_BILINEAR,0);av_opt_set_int(c,"threads",4,0);if(sws_init_context(c,nullptr,nullptr)<0)return 2;for(int n=0;n<20;n++){AVFrame*d=av_frame_alloc();d->buf[0]=av_buffer_create(out.data(),w*h*4+AV_INPUT_BUFFER_PADDING_SIZE,[](void*,unsigned char*){},nullptr,0);d->data[0]=out.data();d->linesize[0]=w*4;d->width=w;d->height=h;d->format=AV_PIX_FMT_RGBA;int r=sws_scale_frame(c,d,s);av_frame_free(&d);if(r<0)return 3;int overwritten=0;for(size_t j=w*h*4+AV_INPUT_BUFFER_PADDING_SIZE;j<out.size();j++)overwritten+=out[j]!=0xCD;if(overwritten){printf("OVERWRITE %dx%d: %d bytes beyond RGBA allocation\n",w,h,overwritten);return 4;}}printf("PASS %dx%d threaded conversion 20 frames\n",w,h);sws_freeContext(c);av_frame_free(&s);} }
