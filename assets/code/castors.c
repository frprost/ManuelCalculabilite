/* castors.c : enumeration exhaustive des machines de Turing a n etats (n<=3), 2 symboles.
   Usage : ./castors n 200 30 3000
   Chaque machine est simulee 200 pas ; si elle ne s arrete pas, on cherche une preuve de
   non-arret (pas de transition d arret, raisonnement arriere, cycle, cycle translate,
   ensemble ferme de n-grammes). Les machines restantes sont ecrites (UNKNOWN) pour
   castors_far.py. La limite de 200 pas ne sert qu a trier : aucune valeur de S n est supposee. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TS 4096
#define MAXN 3
int GMAX=8;
int n; int W[MAXN][2], M[MAXN][2], NX[MAXN][2]; /* NX = n means halt */
static unsigned char tape[TS];
long cnt_cps=0,cnt_halt=0,cnt_cyc=0,cnt_tc=0,cnt_back=0,cnt_nohalt=0,cnt_unknown=0;
int bestS=0,bestSig=0;
/* simulate up to lim steps; return steps if halts (count incl. halting transition), -1 otherwise */
int simulate(int lim,int *ones){
  memset(tape,0,TS); int pos=TS/2,st=0;
  for(int t=1;t<=lim;t++){ int r=tape[pos]; tape[pos]=W[st][r]; int nx=NX[st][r]; pos+=M[st][r]?1:-1; if(nx==n){int c=0;for(int i=0;i<TS;i++)c+=tape[i];*ones=c;return t;} st=nx; if(pos<1||pos>=TS-1) return -2;}
  return -1;
}
/* translated cycler / cycler on records */
#define REC 4000
int rec_t[REC],rec_st[REC],rec_pos[REC],rec_side[REC]; unsigned char *rec_tape[REC];
int histmin[200001],histmax[200001];
int trcycler(int lim){
  memset(tape,0,TS); int pos=TS/2,st=0,lo=pos,hi=pos,nr=0; int ok=0;
  int *hp=malloc(sizeof(int)*(lim+1)); hp[0]=pos;
  for(int t=1;t<=lim && !ok;t++){
    int r=tape[pos]; tape[pos]=W[st][r]; int nx=NX[st][r]; pos+=M[st][r]?1:-1; if(nx==n) break; st=nx; hp[t]=pos;
    if(pos<2||pos>=TS-2) break;
    int side=0; if(pos>hi){hi=pos;side=1;} else if(pos<lo){lo=pos;side=-1;}
    if(side && nr<REC){
      for(int k=nr-1;k>=0 && !ok;k--){ if(rec_side[k]!=side||rec_st[k]!=st) continue;
        int t1=rec_t[k],p1=rec_pos[k];
        if(side==1){ int L=p1; for(int u=t1;u<=t;u++) if(hp[u]<L) L=hp[u]; int D=p1-L; int good=1;
          for(int d=0;d<=D;d++) if(rec_tape[k][p1-d]!=tape[pos-d]){good=0;break;}
          if(good) ok=1; }
        else { int R=p1; for(int u=t1;u<=t;u++) if(hp[u]>R) R=hp[u]; int D=R-p1; int good=1;
          for(int d=0;d<=D;d++) if(rec_tape[k][p1+d]!=tape[pos+d]){good=0;break;}
          if(good) ok=1; }
      }
      rec_t[nr]=t;rec_st[nr]=st;rec_pos[nr]=pos;rec_side[nr]=side; rec_tape[nr]=malloc(TS); memcpy(rec_tape[nr],tape,TS); nr++;
    }
  }
  for(int k=0;k<nr;k++) free(rec_tape[k]); free(hp);
  return ok;
}

static unsigned char snap[TS];
int cycler(int lim){
  memset(tape,0,TS); int pos=TS/2,st=0; int spos=pos,sst=st; memcpy(snap,tape,TS); long power=1,lam=0;
  for(int t=1;t<=lim;t++){
    int r=tape[pos]; tape[pos]=W[st][r]; int nx=NX[st][r]; pos+=M[st][r]?1:-1; if(nx==n) return 0; st=nx;
    if(pos<1||pos>=TS-1) return 0;
    lam++;
    if(st==sst && pos==spos && memcmp(tape,snap,TS)==0) return 1;
    if(lam==power){ power*=2; lam=0; spos=pos; sst=st; memcpy(snap,tape,TS); }
  }
  return 0;
}

/* n-gram closed position set */
int ngram_cps(int g){
  int G=1<<g; static unsigned char Ls[1<<12],Rs[1<<12]; static unsigned char C[3][1<<12][2][1<<12];
  if(g>12) return 0;
  memset(Ls,0,G);memset(Rs,0,G);
  for(int q=0;q<n;q++)for(int l=0;l<G;l++)for(int c=0;c<2;c++)memset(C[q][l][c],0,G);
  Ls[0]=Rs[0]=1; C[0][0][0][0]=1;
  int changed=1;
  /* n-gram encoded as bits: for l, bit (g-1) is farthest-left? define l as integer whose bit 0 = cell adjacent to head (left side) ; r bit0 = cell adjacent right */
  while(changed){ changed=0;
    for(int q=0;q<n;q++)for(int l=0;l<G;l++)if(Ls[l])for(int c=0;c<2;c++)for(int r=0;r<G;r++){
      if(!C[q][l][c][r]) continue;
      if(NX[q][c]==n) return 0;
      int w=W[q][c],nq=NX[q][c];
      if(M[q][c]){ /* move right: new left = (l<<1|w) & mask ; new head = r bit0 ; new right = r>>1 | b<<(g-1) */
        int nl=((l<<1)|w)&(G-1); if(!Ls[nl]){Ls[nl]=1;changed=1;}
        int nc=r&1;
        for(int b=0;b<2;b++){ int nr=(r>>1)|(b<<(g-1)); if(!Rs[nr]) continue; if(!C[nq][nl][nc][nr]){C[nq][nl][nc][nr]=1;changed=1;} }
      } else {
        int nr=((r<<1)|w)&(G-1); if(!Rs[nr]){Rs[nr]=1;changed=1;}
        int nc=l&1;
        for(int b=0;b<2;b++){ int nl=(l>>1)|(b<<(g-1)); if(!Ls[nl]) continue; if(!C[nq][nl][nc][nr]){C[nq][nl][nc][nr]=1;changed=1;} }
      }
    }
  }
  return 1;
}
/* backward reasoning */
#define BW 64
int bdepth;
int back(int st,int pos,int *kp,int *kv,int nk,int depth){
  /* returns 1 if refuted (all predecessors die), 0 if could not refute */
  /* if consistent with initial config: state 0, all known cells blank */
  if(st==0){ int allb=1; for(int i=0;i<nk;i++) if(kv[i]){allb=0;break;} if(allb) return 0; }
  if(depth>=bdepth) return 0;
  for(int s=0;s<n;s++) for(int r=0;r<2;r++){
    if(NX[s][r]!=st) continue;
    int ppos=pos-(M[s][r]?1:-1);
    /* cell ppos after write must be W[s][r] if known */
    int idx=-1; for(int i=0;i<nk;i++) if(kp[i]==ppos) idx=i;
    if(idx>=0 && kv[idx]!=W[s][r]) continue;
    int kp2[BW],kv2[BW],nk2=0; for(int i=0;i<nk;i++){kp2[nk2]=kp[i];kv2[nk2]=kv[i];nk2++;}
    if(idx>=0) kv2[idx]=r; else { if(nk2>=BW) return 0; kp2[nk2]=ppos;kv2[nk2]=r;nk2++; }
    if(!back(s,ppos,kp2,kv2,nk2,depth+1)) return 0;
  }
  return 1;
}
int backward(){
  for(int s=0;s<n;s++) for(int r=0;r<2;r++) if(NX[s][r]==n){ int kp[BW]={0},kv[BW]={r}; if(!back(s,0,kp,kv,1,0)) return 0; }
  return 1;
}
int main(int argc,char**argv){
  n=atoi(argv[1]); int lim=atoi(argv[2]); bdepth=atoi(argv[3]); int big=atoi(argv[4]); if(argc>5) GMAX=atoi(argv[5]);
  int ntr=2*n; long total=1; for(int i=0;i<ntr;i++) total*=4*(n+1);
  for(long code=0;code<total;code++){
    long c=code; int hasH=0;
    for(int s=0;s<n;s++) for(int r=0;r<2;r++){ int v=c%(4*(n+1)); c/=4*(n+1); W[s][r]=v&1; M[s][r]=(v>>1)&1; NX[s][r]=v>>2; if(NX[s][r]==n) hasH=1; }
    int ones; int st=simulate(lim,&ones);
    if(st>0){ cnt_halt++; if(st>bestS)bestS=st; if(ones>bestSig)bestSig=ones; continue; }
    if(!hasH){cnt_nohalt++; continue;}
    if(backward()){cnt_back++;continue;}
    if(cycler(big)){cnt_cyc++;continue;}
    if(trcycler(big)){cnt_tc++;continue;}
    { int okc=0; for(int g=1;g<=GMAX&&!okc;g++) if(ngram_cps(g)) okc=1; if(okc){cnt_cps++;continue;} }
    cnt_unknown++;
    if(1){ printf("UNKNOWN code %ld:",code); for(int s=0;s<n;s++)for(int r=0;r<2;r++)printf(" %d%c%c",W[s][r],M[s][r]?'R':'L',NX[s][r]==n?'H':'A'+NX[s][r]); printf("\n"); }
  }
  printf("n=%d total=%ld halt=%ld (S=%d Sigma=%d) nohaltTrans=%ld backward=%ld cycler=%ld transcycler=%ld cps=%ld unknown=%ld\n",n,total,cnt_halt,bestS,bestSig,cnt_nohalt,cnt_back,cnt_cyc,cnt_tc,cnt_cps,cnt_unknown);
}
