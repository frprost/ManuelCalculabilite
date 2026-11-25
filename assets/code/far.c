/* far.c : meme critere que castors_far.py (gauche abstraite par un automate fini deterministe D,
   droite exacte comme une pile, saturation post*), reecrit en C pour essayer des automates plus grands.
   Entree : une machine par ligne, 8 transitions "1RB" ou "---" (non definie = arret possible).
   Usage : ./castors_tnf 4 1000 30 5000 | grep UNKNOWN | sed "s/UNKNOWN: //" | ./far 5
   puis ./far 6 6 sur les machines restantes (NON DECIDE). NMIN (2e argument, facultatif)
   est la plus petite taille d automate essayee. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NS 4
#define MAXQ 6
#define MAXST 1200
#define WORDS ((MAXST+63)/64)
typedef unsigned long long u64;
int nf; int TW[NS][2],TM[NS][2],TN[NS][2],TD[NS][2]; /* TD=1 si defini */
int nq; int dl[MAXQ][2];
static u64 tr[MAXST][4][WORDS]; /* 0,1,2=BOT,3=EPS */
int nstates, FIN;
typedef struct {int p,g,p2,np,a,b;} Rule; Rule R[20000]; int nr;
int midid[MAXST][3];
int ctl(int q,int f){return q*nf+f;}
int newstate(){return nstates++;}
int add(int s,int a,int t){ u64 m=1ULL<<(t&63); if(tr[s][a][t>>6]&m) return 0; tr[s][a][t>>6]|=m; return 1; }
/* reach: states t with s -eps*-> s' -g-> t */
void reach(int s,int g,u64*out){
  u64 seen[WORDS]={0}; int st[MAXST],sp=0; seen[s>>6]|=1ULL<<(s&63); st[sp++]=s; memset(out,0,sizeof(u64)*WORDS);
  while(sp){ int x=st[--sp]; for(int w=0;w<WORDS;w++){ out[w]|=tr[x][g][w]; u64 e=tr[x][3][w]&~seen[w]; while(e){int b=__builtin_ctzll(e); e&=e-1; int y=w*64+b; seen[w]|=1ULL<<b; st[sp++]=y;} } }
}
int getmid(int p2,int a){ if(midid[p2][a]<0) midid[p2][a]=newstate(); return midid[p2][a]; }
int check(){
  nstates=nq*nf; nr=0;
  for(int q=0;q<nq;q++)for(int f=0;f<nf;f++)for(int r=0;r<2;r++){ if(!TD[f][r]) continue; int w=TW[f][r],t=TN[f][r];
    if(TM[f][r]){ R[nr++]=(Rule){ctl(q,f),r,ctl(dl[q][w],t),0,0,0}; if(r==0) R[nr++]=(Rule){ctl(q,f),2,ctl(dl[q][w],t),1,2,0}; }
    else for(int q2=0;q2<nq;q2++)for(int b=0;b<2;b++){ if(dl[q2][b]!=q) continue;
      R[nr++]=(Rule){ctl(q,f),r,ctl(q2,t),2,b,w};
      if(r==0){ int X=newstate(); R[nr++]=(Rule){ctl(q,f),2,X,2,w,2}; R[nr++]=(Rule){X,w,ctl(q2,t),2,b,w}; } } }
  FIN=newstate();
  int base=nstates; /* mid states allocated afterwards */
  for(int i=0;i<base;i++) for(int a=0;a<3;a++) midid[i][a]=-1;
  for(int i=0;i<MAXST;i++) memset(tr[i],0,sizeof(tr[i]));
  add(ctl(0,0),2,FIN);
  int ch=1; u64 out[WORDS];
  while(ch){ ch=0;
    for(int k=0;k<nr;k++){ Rule*u=&R[k]; reach(u->p,u->g,out);
      for(int w=0;w<WORDS;w++){ u64 e=out[w]; while(e){ int b=__builtin_ctzll(e); e&=e-1; int s=w*64+b;
        if(u->np==0) ch|=add(u->p2,3,s);
        else if(u->np==1) ch|=add(u->p2,u->a,s);
        else { int m=getmid(u->p2,u->a); if(nstates>=MAXST){fprintf(stderr,"MAXST\n");exit(1);} ch|=add(u->p2,u->a,m); ch|=add(m,u->b,s); } } } } }
  for(int q=0;q<nq;q++)for(int f=0;f<nf;f++)for(int r=0;r<2;r++) if(!TD[f][r]){
    reach(ctl(q,f),r,out); for(int w=0;w<WORDS;w++) if(out[w]) return 0;
    if(r==0){ reach(ctl(q,f),2,out); for(int w=0;w<WORDS;w++) if(out[w]) return 0; } }
  return 1;
}
/* automates canoniques : delta(0,0)=0, etats numerotes par ordre de decouverte en largeur */
int canon(){ int ord[MAXQ],seen[MAXQ]={0},k=1,h=0; ord[0]=0; seen[0]=1;
  while(h<k){ int x=ord[h++]; for(int b=0;b<2;b++){ int y=dl[x][b]; if(!seen[y]){ if(y!=k) return 0; seen[y]=1; ord[k++]=y; } } }
  return k==nq; }
int trydfas(){
  int cells=2*nq-1; long tot=1; for(int i=0;i<cells;i++) tot*=nq;
  for(long c=0;c<tot;c++){ long x=c; dl[0][0]=0; for(int i=1;i<2*nq;i++){ dl[i/2][i%2]=x%nq; x/=nq; }
    if(!canon()) continue; if(check()) return 1; }
  return 0;
}
int main(int argc,char**argv){
  int NMAX=atoi(argv[1]); int NMIN=argc>2?atoi(argv[2]):1; char t[8][8]; nf=NS; int nd=0,tot=0;
  while(scanf("%s %s %s %s %s %s %s %s",t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7])==8){ tot++;
    int res=0,side=0;
    for(int n=NMIN;n<=NMAX&&!res;n++) for(int mir=0;mir<2&&!res;mir++){
      for(int i=0;i<8;i++){int s=i/2,r=i%2; TD[s][r]=t[i][0]!='-'; if(!TD[s][r]) continue; TW[s][r]=t[i][0]-'0'; TM[s][r]=(t[i][1]=='R')^mir; TN[s][r]=t[i][2]-'A';}
      nq=n; if(trydfas()){res=n;side=mir;}
    }
    printf("%s %s %s %s %s %s %s %s -> %s\n",t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],res?(side?"prouvee (miroir)":"prouvee"):"NON DECIDE"); fflush(stdout);
    if(!res) nd++;
  }
  printf("%d machines, %d prouvees sans arret, %d non decidees\n",tot,tot-nd,nd);
}
