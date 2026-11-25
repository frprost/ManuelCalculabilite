/* castors_tnf.c : enumeration exhaustive des machines de Rado a n etats (n<=4), 2 symboles,
   en "forme normale arborescente". Une machine n est definie que sur les transitions qu elle
   emploie : quand la simulation atteint une transition non definie, on ramifie (arret a cet
   endroit, ou toute ecriture, tout deplacement, tout etat deja employe ou un seul etat neuf).
   Le premier deplacement est vers la droite (symetrie miroir). Toute machine se ramene ainsi
   a une feuille de l arbre, a renumerotation des etats et miroir pres.
   Usage : ./castors_tnf 4 1000 30 5000
   Une feuille qui ne s arrete pas en 1000 pas recoit une preuve de non-arret (raisonnement
   arriere, cycle, cycle translate, n-grammes), les transitions non definies comptant comme
   des arrets possibles. Les feuilles restantes (UNKNOWN) sont passees a far.c.
   La limite de 1000 pas ne sert qu a trier : aucune valeur de S n est supposee. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TS 4096
#define MAXN 4
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
  int G=1<<g; static unsigned char Ls[1<<12],Rs[1<<12]; static unsigned char C[MAXN][1<<12][2][1<<12];
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

int LIM,BIG; long leaves=0;
int nused;
void record_unknown(){
  printf("UNKNOWN:"); for(int s=0;s<n;s++)for(int r=0;r<2;r++){ if(NX[s][r]==n) printf(" ---"); else printf(" %d%c%c",W[s][r],M[s][r]?'R':'L','A'+NX[s][r]);} printf("\n");
}
/* simulate: returns step t>0 at which an undefined transition (NX==n) is met (state,symbol in *us,*ur), or -1 */
int sim2(int lim,int *us,int *ur,int *ones){
  memset(tape,0,TS); int pos=TS/2,st=0;
  for(int t=1;t<=lim;t++){ int r=tape[pos];
    if(NX[st][r]==n){ *us=st;*ur=r; tape[pos]=1; int c=0; for(int i=0;i<TS;i++)c+=tape[i]; *ones=c; return t; }
    tape[pos]=W[st][r]; pos+=M[st][r]?1:-1; st=NX[st][r]; if(pos<1||pos>=TS-1) return -2; }
  return -1;
}
int ndef(){int k=0;for(int s=0;s<n;s++)for(int r=0;r<2;r++)if(NX[s][r]<n)k++;return k;}
void explore(){
  int us,ur,ones; int t=sim2(LIM,&us,&ur,&ones);
  if(t>0){
    /* child "halt": the machine halts at step t */
    cnt_halt++; leaves++; if(t>bestS)bestS=t; if(ones>bestSig)bestSig=ones;

    int used=0; for(int s=0;s<n;s++)for(int r=0;r<2;r++) if(NX[s][r]<n && NX[s][r]+1>used) used=NX[s][r]+1; if(used<us+1) used=us+1;
    int maxst = used<n? used+1 : n;
    for(int w=0;w<2;w++)for(int m=0;m<2;m++)for(int q=0;q<maxst;q++){
      if(ndef()==0 && m==0) continue; /* mirror symmetry: first move to the right */
      W[us][ur]=w;M[us][ur]=m;NX[us][ur]=q;
      if(ndef()==2*n){ /* no transition left undefined: no halting transition */ cnt_nohalt++; leaves++; }
      else explore();
      NX[us][ur]=n;
    }
    return;
  }
  leaves++;
  if(t==-2){ cnt_unknown++; record_unknown(); return; }
  if(backward()){cnt_back++;return;}
  if(cycler(BIG)){cnt_cyc++;return;}
  if(trcycler(BIG)){cnt_tc++;return;}
  { int okc=0; for(int g=1;g<=GMAX&&!okc;g++) if(ngram_cps(g)) okc=1; if(okc){cnt_cps++;return;} }
  cnt_unknown++; record_unknown();
}
int main(int argc,char**argv){
  n=atoi(argv[1]); LIM=atoi(argv[2]); bdepth=atoi(argv[3]); BIG=atoi(argv[4]); if(argc>5) GMAX=atoi(argv[5]);
  for(int s=0;s<n;s++)for(int r=0;r<2;r++) NX[s][r]=n;
  explore();
  printf("n=%d feuilles=%ld arret=%ld (S=%d Sigma=%d) sans_arret=%ld arriere=%ld cycle=%ld cycle_translate=%ld ngrammes=%ld inconnues=%ld\n",n,leaves,cnt_halt,bestS,bestSig,cnt_nohalt,cnt_back,cnt_cyc,cnt_tc,cnt_cps,cnt_unknown);
}
