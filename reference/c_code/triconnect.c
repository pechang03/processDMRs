/*******************************************************************************
+  Copyright (c) 1991-2000  by Peter Shaw
+  All rights reserved.
+ 
*******************************************************************************/
//------------------------------------------------------------------------------
// TRI-EDGE-CONNECTED COMPONENTS
//                                                                              
// last modified: 
//
//
//------------------------------------------------------------------------------
#ifdef LEDA51
#include <LEDA/graph/graph.h>
#include <LEDA/graph/graph_alg.h>
#include <LEDA/graph/graph_misc.h>
//#include <LEDA/node_set.h>
#include <LEDA/graph/node_array.h>
#include <LEDA/graph/graph_iterator.h>
//#include <LEDA/stack.h>
#include <LEDA/graphics/graphwin.h>
#include <iostream>
using std::cout;
using std::endl;
using std::istream;
using std::ifstream;
using std::ostream;
using std::ofstream;
using namespace leda;
#else
#include <LEDA/graph.h>
#include <LEDA/graph_alg.h>
#include <LEDA/graph_misc.h>
//#include <LEDA/node_set.h>
#include <LEDA/node_array.h>
#include <LEDA/graph_iterator.h>
//#include <LEDA/stack.h>
#include <LEDA/graphwin.h>
#include <iostream.h>
#include <stdio.h>
#endif
#define DISP
//#define DISP2

typedef list<node> path;
typedef list<edge> epath;

GraphWin *gwpt;
void ContinueButton(GraphWin& gw);

void ContinueButton(GraphWin& gw)
{ window& W = gw.get_window();

  panel P;

  //P.set_panel_bg_color(win_p->mono() ? white : ivory);
  P.button("Continue");
  W.disable_panel();
  P.open(W,10,10);
  W.enable_panel();
}


static void triedge_dfs(GRAPH<node,edge>& G, node_array<path> & sigma, node w, node v,
            node_array<int>& pre,
	    int count1, int &count2, node_array<int>& lowpt,
            node_array<node>& father, list<node>& P, int &cols) ;
void AbsorbPath(GRAPH<node,edge> &G, node_array<path>& sigma, int &cols, path & P, node w, node u);
void AbsorbPath(GRAPH<node,edge> &G, node_array<path>& sigma, int &cols, path & P );
void print_lists(path const & Pw, path const &Pu);
int split_graph(graph &G, node_array<int> components,
                list<edge>& bridges, array<path>& sigma, list<edge>& deg1edges);
void CopyInducedGraph(GRAPH<node,edge>& H, const graph& G, const list<node>& V);

int read_dim(graph &G, istream& in);
void write_dim(graph &G, ostream& out);
void write_dim(GRAPH<node,edge> &G, ostream& out);

//node_array<int> sigma;
//static int count;
//static int cols;

int TRICONNECTED_COMPONENTS(graph& G , list<edge>& cut_edges, list<edge>& bridges, array<path>& sigma3, list<edge>& deg1edges)
{
  // computes the triconnected components of the underlying  undirected
  // graph,  returns m = number of biconnected components and 
  // in edge_array<int> compnum for each edge an integer with
  // compnum[x] = compnum[y] iff edges x and y belong to the same component 
  // and 0 <= compnum[e] <= m-1 for all edges e
  // running time : O(|V|+|E|)
  //
  
   int count1 = 0;
   int cols = 1;
   int cnumb=0;
  // CHANGE to paramererized subgraph, then map back trivial GRAPH<node,edge> H;
   int num2comp=1;
   node_array<int> ncomp(G,-1);
   //list<edge> thebridges;
   array<path> sigma2;
   node n;
   edge e;
   int origsizeG = G.number_of_edges();
   if (Is_Connected(G)) {
         cout << "Input Graph is connected\n";
   } else {
         cout << "Input Graph is NOT connected\n";
   }
   if(!Is_Biconnected(G)) {
      cout <<"Graph is not biconnected \n";
      num2comp = split_graph(G, ncomp, bridges, sigma2, deg1edges);
      cout  << "Split into Num Components " << num2comp << endl;
#ifndef TRIM
      forall(e, bridges) {
         if(!G.is_hidden(e)) {
            cout << "Bridge not removed\n";
            exit(0);
         }
      }
#endif
   } else {
      cout <<"Input Graph is biconnected \n";
      sigma2.resize(1); 
      path &n2complist= sigma2[0];
      num2comp=1;
      n2complist = G.all_nodes();
   }

   int i;
   node_array<int>  compnum(G,-1);
   int numcutedges=0;
   int ttlnumberedges=0;
   for(i=0 ;i<num2comp ; i++) {
      list<node>& n2complist = sigma2[i];
      GRAPH<node,edge> H;
      CopyInducedGraph(H, G, n2complist);
      ttlnumberedges+=H.number_of_edges(); // parity check on number of edges
      //If the subgraph is an isolated vertex , or edge then no need to test it
      //For connectivity
      if (H.number_of_nodes() <= 1) {
         node r = H.first_node();
         if(r != NULL) {
            cout << "Subgraph " <<i << " is an isolated vertex\n";
            sigma3.resize(cnumb+1);
	    list<node> &ncomplist= sigma3[cnumb];
            ncomplist.push(H[r]);   
	    cnumb++;
         }
         continue;
      }
      //This could easily be increated to test for cliques
      if (H.number_of_edges() == 1) {
         cout << "WARNING subgraph is not biconnected\n";
         node r = H.first_node();
         n = H.last_node();
         if(r != NULL) {
            cout << "Subgraph is an isolated edge\n";
            sigma3.resize(cnumb+1);
	    list<node> &ncomplist= sigma3[cnumb];
            ncomplist.push(H[r]);   
            ncomplist.push(H[n]);   
	    cnumb++;
         }
         continue;
      }

      cout << "Num nodes in subgraph " << i << " is "<< H.number_of_nodes() << endl;
      cout << "Num edges in subgraph " << i << " is "<< H.number_of_edges() << endl;
      //node_array<int>  compnum(H,-1);
      // Some basic stats on the graph
      int numdeg2=0;
      int numdeg1=0;
      //We really shoudln't have any degree 2 nodes here if we do they should
      // be removed and processes differently.
      forall_nodes(n,H) {
         if(H.degree(n) <= 1) {
            numdeg1++;
            cout << "Node " <<n->id() << "is deg less than 2\n";
         }
         if(H.degree(n) == 2) {
            numdeg2++;
            e=G.first_adj_edge(n);
            //G.hide_edge(e);
            e=G.last_adj_edge(n);
            //G.hide_node(n);
            //cout << "Node " <<n->id() << "is deg 2\n";
         }
      }
      cout << "Biconnected Subgraph "<< i <<" has "<<numdeg2<< " small deg 2 nodes "<<endl;
      cout << "Number of small <=1 deg nodes in subgraph " << numdeg1 << endl;
#ifdef DISP
   GraphWin gw(H,"Triconnected Search");
   gwpt = &gw;
   gw.display();
   gw.set_directed(false);

   gw.set_node_label_type(user_label);
   gw.set_node_width(35);

   // gw.set_node_color(grey);
   node v;
   forall_nodes(v,H) {
    //Check this for memory problems      
      string a = string("%d",v->id());
      gw.set_user_label(v,a);
   }

   gw.update_graph();
   gw.edit();

   ContinueButton(gw);
#endif
      //Choose a root node of degree > 2
      node r = H.first_node();
      while(r != NULL && H.degree(r) <=2) {
         r=H.succ_node(r);
      }
      if(r == NULL) {
         cout << "Subgraph is a cycle\n";
	 //Map the nodes in this subgraph back into the original graph
	 //and append them to the next component list
         sigma3.resize(cnumb+1);
	 list<node> nsubglist = H.all_nodes();
	 list<node> &ncomplist= sigma3[cnumb];
	 forall(n, nsubglist) {
            ncomplist.push(H[n]);   
	 }
	 cnumb++;
         continue;
      }
      //cout << "r=" << r->id()  << " has degree" << H.degree(r) 
      //     << "length" << H.adj_nodes(r).length() << endl;

      //Split the next biconnected component into triconnected components
      node_array<int> pre(H,-1); //pre == dfsnum
      node_array<int> lowpt(H,0);
      node_array<node> father(H,NULL);
      list<node> P;
      int count2 = 0;
      node_array<path> sigma;
      sigma.init(H);
      node n;
      forall_nodes(n, H) {
         sigma[n].push(n);
      }

      triedge_dfs(H, sigma, r,NULL,
      	           pre, count1, count2, lowpt, father, P, cols); 
      // Replace the edges removed by algorithm
//      H.restore_all_edges();
      list<node> nlist;  //List containing the nodes in each component
      //edge e;
      int cnum=0; // The component number
      forall_nodes(n,H) {
         //nlist = sigma[n];
         list<node> &nsubglist = sigma[n];
         if (!nsubglist.empty()) {
            //Map the nodes in this subgraph back into the original graph
            //and append them to the next component list
	    //Warning Potential complexity blowout in resize
            sigma3.resize(cnumb+1);
            list<node> &ncomplist= sigma3[cnumb];
            //cout << "Sigma n=" << n->id()  <<"=[";
            node v,x;
            forall(v, nsubglist) {
               cout << v->id() << ", ";
               x=H[v];
               ncomplist.push(x);   
               //compnum[v] = cnum;
               compnum[x] = cnumb;
            }
            //cout << "]\n";
            cnumb++;
            cnum++;
         }
      }
      cout << "Number of 3-edge-connected components in subgraph " << i 
           << " is : " << cnum << endl;
   }
   if(origsizeG - (ttlnumberedges + bridges.length()) != 0) {
      cout << "Error in the size of subgraphs\n";
   }
   forall_edges(e, G) {
         //cout << "edge" << source(e)->id() << "-" << target(e)->id() << endl;
         //cout << "comp" << compnum[source(e)] <<"|"<< compnum[target(e)]<< endl ;
      if(!G.is_hidden(e) && compnum[source(e)] != compnum[target(e)]) {
         cut_edges.push(e);
   	 numcutedges++;
      }
   }
   cout << "Total number of components : " << cnumb << endl;
   cout << "Total number of cut-edges  : " << cut_edges.length() << endl;
  
   cout << "FINISHED" << endl;
   return cnumb;
} //TRICONNECTED_COMPONENT

static void triedge_dfs(GRAPH<node,edge>& G,node_array<path> & sigma,  node w, node v,
            node_array<int>& pre,
	    int  count1, int &count2, node_array<int>& lowpt,
            node_array<node>& father, list<node> & Pw, int &cols) {
   pre[w] = count2;
   count2++;
   //count1++;
   father[w] = v;
   lowpt[w] = pre[w];
   //P[w].clear(); P[w].append(w);
   node u=NULL,z=NULL,x;
   edge ewu, nxte, euz;
   path Pu;
   Pw.push(w);
   //cout << "Proc node " << w->id() << " size " << G.number_of_edges() << endl;
#ifdef DISP
	   string b = string("%d|%d,%d",w->id(),pre[w],lowpt[w]);
	   gwpt->set_user_label(w,b);
	   if (v != NULL)
	      gwpt->set_color(v,red);
	   gwpt->set_color(w,blue);
	   gwpt->update_graph();
	   ContinueButton(*gwpt);
#endif   
   //for(ewu=First_Adj_Edge(w,0);ewu!= NULL;ewu=e2)
   for(int dinout=0;dinout==0;dinout++)
   for(ewu=First_Inout_Edge(w,dinout);ewu!=nil;ewu=nxte) {
      u = G.opposite(w,ewu);
      //cout << "   Proc edge" << w->id() <<"-" << u->id() << "->" << ewu->id() << endl;
      nxte=Succ_Inout_Edge(ewu,w,dinout);
      if(G.is_hidden(ewu)) {
            //cout << " main loop Attempt to process hidden edge\n";
            //This is caused by backedges to w being removed in AbsorbPath
            //The alterative is make them self loops and then remove them
            //when they are encounted.
            continue; //Blugin it to work for the moment.
      }

      //Is this what should be done ?
#if 0
      while( nxte != NULL && G.opposite(w,nxte) == u) {
         // if nxte == NULL then ewu should then be set correctly to First_Inout_Edge
         //We have a self loop
         edge nxxt = nxte;
         G.hide_edge(nxte);
         cout <<" skipping self loop [" << w->id() <<"," << u->id() << "]" << endl;
         continue;
      }
      //cout << "found next after self loop\n";
#endif
      if(u == NULL) {
         cout << " invalid node u\n";
         exit(0);
      }
      //e2=G.adj_succ(ewu);
      //Skip the parent node
      if(u == v) {
        continue;
      }
      if(u == w) {
         //Self loop 
         //G.del_edge(ewu);
#ifndef TRIM
         if(G.is_hidden(ewu)) {
            cout << "Attempt to hide hidden edge\n";
            exit(1);
         }
#endif
         G.hide_edge(ewu);
         break;
      }
      //cout << "--   Proc edge" << w->id() <<"-" << u->id() << "->" << ewu->id() << endl;
      if(G.degree(u) < 2) {
         //cout << "w="<< w->id() << " deg ="<< G.degree(u) << "node " << u->id() << " <2\n";
#ifdef DISP
   gwpt->update_graph();
   ContinueButton(*gwpt);
#endif  
         // If degree u == 0 this is a moved edges that was nxte;
   //      exit(0);
         continue;
      }
      //cout << "   Proc edge" << w->id() <<"-" << u->id() << "->" << ewu->id() << endl;
      if (pre[u] < 0 ) {
	 triedge_dfs(G, sigma, u, w, pre, count1, count2 ,lowpt, father, Pu, cols);
         //cout << "   post Proc edge" << w->id() <<"-" << u->id() << "->" << ewu->id() << endl;
         //cout << "Non back edge\n";
         //print_lists(Pw,Pu);
#ifdef DISP
	   gwpt->set_color(u,green);
	   string a = string("%d|%d,%d",w->id(),pre[w],lowpt[w]);
	   gwpt->set_user_label(w,a);
	   string b = string("%d|%d,%d",u->id(),pre[u],lowpt[u]);
	   gwpt->set_user_label(u,b);
	   if (v != NULL)
	      gwpt->set_color(v,red);
	   gwpt->set_color(w,blue);
	   gwpt->update_graph();
	   ContinueButton(*gwpt);
#endif   
	 if (G.degree(u) == 2) { //These edges should correspond to cut-edges an
				//Are probably what we want to remove
	    //Tsin meaning of G\e is similar to contract the edge e
            //cout << "deleting edge" << w->id() <<"-" << target(ewu)->id() << "->" << ewu->id() << endl;
#ifndef TRIM
            if(G.is_hidden(ewu)) {
               cout << "Attempt to hide hidden edge\n";
               //exit(1);
            }
#endif
	    G.hide_edge(ewu);
#ifdef DISP
            gwpt->update_graph();
#endif
            //cout << "deleted deg2 edge\n";
            euz=G.first_adj_edge(u);
	    z = opposite(u,euz); 
            //cout << "moving edge\n";
            //cout << euz->id() << "(" << source(euz)->id() << "-" << target(euz)->id() << ") to [" << w->id() << "," << z->id() << "]"<< endl;
#ifndef TRIM
            if(u ==z) {
               cout << " attempting to move self loop\n";
               exit(0);
            }
#endif
            G.move_edge(euz,w,z);
	    x = Pu.pop_front(); // Alternatively use Pu.remove(u)
#ifndef TRIM
            if ( x != NULL && x != u ) {
               cout << "Pu = Pu -u failed" << endl;
               exit(0);
            }
#endif
#if 0 // break loop
            if (ewu) {
              nxte=Succ_Inout_Edge(ewu,w,dinout);
            } else {
              nxte = NULL;
            }
#endif
            //cout << "contracted edge\n";
	 }// else { 
         
  	    if (lowpt[w] <= lowpt[u]) { //deg =2 and lowpt(w) < lowpt(u) should be exlusive
               //cout << "Absorbing w+Pu\n";
               Pu.push_front(w);
	       AbsorbPath(G, sigma, cols,  Pu);
#ifndef TRIM
               if ( !Pu.empty()) {
                  cout << "Pu not empty" << endl;
                  exit(0);
               }
#endif
	    } else {
	         lowpt[w] = lowpt[u]; //update lowpt(w)
#if 0
               if (pre[u] < lowpt[w]) { 
                 cout << "Absorbing2 Pw\n";
	           cout << "Pw Length=" << Pw.length() << endl;
                  AbsorbPath(G, sigma, cols, Pw);
	          lowpt[w] = pre[u];
                  Pw.clear(); Pw.append(w); //Update Pw path
	       } else {
#endif
                //cout << "Absorbing Pw\n";
#ifdef DISP   
   string a = string("%d|%d,%d",v->id(),pre[w],lowpt[w]);
   gwpt->set_user_label(v,a);
#endif
	          AbsorbPath(G, sigma, cols,  Pw);
#ifndef TRIM
                  if ( !Pw.empty()) {
                     cout << "Pw not empty" << endl;
                     exit(0);
                  }
#endif
	          //cout << "Pw = w+Pu" << Pw.length() << endl;
	          Pw.conc(Pu);
	          Pw.push_front(w);       //update Pw path add w to front of list
//	       }
            }
//         } // cut the else
         //print_lists(Pw,Pu);
      } else {
         //cout << "backedge\n"; cout << "Pw:=" ;
         //forall(x,Pw) cout << x->id() <<"-";
         //cout << endl;
#ifdef DISP
	   gwpt->set_color(u,green);
	   string a = string("%d|%d,%d",w->id(),pre[w],lowpt[w]);
	   gwpt->set_user_label(w,a);
	   string b = string("%d|%d,%d",u->id(),pre[u],lowpt[u]);
	   gwpt->set_user_label(u,b);
	   if (v != NULL)
	      gwpt->set_color(v,red);
	   gwpt->set_color(w,blue);
	   gwpt->update_graph();
	   ContinueButton(*gwpt);
#endif
	 if ( pre[u] < pre[w]){ //(w,u) is an outgoing back-edge of w.
                                // should be > but is this the right test 
            // lowpt[w] is always < pre[w] so correct test for
            // should be pre[u] < pre[w]
	    //cout << "Outgoing back-edge - Absorbing Pw" << pre[w] <<">" << pre[u]<< endl;

            if (pre[u] < lowpt[w]) { 
	       //cout << "Pw Length=" << Pw.length() << endl;
               AbsorbPath(G, sigma, cols, Pw);
	       lowpt[w] = pre[u];
               Pw.clear(); Pw.append(w); //Update Pw path
	    } else {
               if (pre[u] < lowpt[w]) { 
	          lowpt[w] = pre[u];
                  cout << "Strange Backedge" << endl;
               }
               //G.hide_edge(ewu);
            }
	 } else {
	    //cout << "Incoming back-edge pre[w] =" 
            //     << pre[w]<< " < pre[u]="<< pre[u] <<  endl;
	    if( pre[u] > pre[w] /*(w,u)is an incoming back-edge of w */ ) { 
	       AbsorbPath(G, sigma, cols, Pw, w,u);
               // Don't do this!!Pw.push(u); 
               //G.del_edge(ewu);
	    } 
            if (pre[u] < lowpt[w]) { 
	       lowpt[w] = pre[u];
               cout << "unexpected Backedge" << endl;
            }
         }
         //print_lists(Pw,Pu);
      }
      //cout << "edge ewu id=" << ewu->id() << "(" << source(ewu)->id() 
      //     << "-" << target(ewu)->id() << ") should match [" << w->id()
      // << "," << u->id() << "]"<< endl;

      // Don't panic just delete and continue at beginning of loop
   }
}

//Absorb that path P
//P is the list of nodes  x0 - x1 - ... - xk
void AbsorbPath(GRAPH<node,edge> & G, node_array<path>& sigma,int &cols,  path & P){
   if (P.empty()) return;
   edge e = NULL, nxte;
   node x0 = P.head();
   node xi,xm1,z,xp1;
   //cout << "P:=" ; forall(xi,P) cout << xi->id() <<"-"; cout << endl; 

   xm1 = P.Pop();
      xp1=NULL;
   if(P.empty()) return;
   while(xm1 != x0 && xm1 != NULL) { // stops if only w in P list
      xi=xm1;
      xm1=P.Pop();
      //cout << "    absorbing "<< xi->id() <<" #" << xm1->id() << endl;
      //cout << "sigma" << xi->id() << " length="<< sigma[xi].length() << endl;
      sigma[x0].conc(sigma[xi]); 
      //cout << "Added to sigma" << x0->id() << " length="<< sigma[x0].length() << ":=";
      //node n; forall(n,sigma[x0]) cout <<n->id() <<" ";
      //cout << endl;
      //Note there is a better way to do this not supported by current LEDA
      for(int dinout=0;dinout==0;dinout++)
      for(e=First_Inout_Edge(xi,dinout);e!=nil;) {
         nxte=Succ_Inout_Edge(e,xi,dinout);
         z = G.opposite(xi,e);//by differentiating between in and out edges this
         //cout << "      Proc" << z->id() << "to " << x0->id() << endl;
	 if ( z == xm1 /*|| z==xp1*/ || z == x0) { 
            //cout << "      removing " << "z=" << z->id() << ":" << e->id() <<"[" << source(e)->id() <<"-" << target(e)->id() <<"]" << endl;
            //G.del_edge(e);
#ifndef TRIM
            if(G.is_hidden(e)) {
               cout << "Attempt to hide hidden edge\n";
               exit(1);
            }
#endif
            //Rather than deleting the back edge make it a self loop so that the
            //next edge can be found still
            G.hide_edge(e);
#ifdef DISP
            gwpt->update_graph();
#endif
 
	 } else {
            //cout << "      Moving" << xi->id() << "- " << z->id() << "to " << z->id() << "-" << x0->id() << endl;
            if(source(e) == target(e)) {
               cout << " attempting to move self loop2\n";
               exit(0);
            }
            G.move_edge(e,x0,z);
	 }
         e=nxte;
         xp1=xi;
      }     
         
   }
}

//Absorb that path from w to u including w and u
void AbsorbPath(GRAPH<node,edge> & G, node_array<path>& sigma, int& cols, path & P,node u, node v) {
   if (P.empty()) return;
   edge e = NULL,nxte;
   node x0 = P.head();
   // check u should be the first element in the list.
   node xi,xm1,z,xp1;//xm1 = x_{i-1}, xi is x_i, z is a node adjacent to x_i
                     // and xp1 is the other neibour to xi (other than xm1) if there is one in Pw
   list_item itn1,itn2;
   //cout << "P[u,v] (P[w,u]):=" ;
   //forall(xi,P) cout << xi->id() <<"-"; cout << endl;
#ifndef TRIM
   if( x0 != u) {
      cout << "u=" << u->id()<<" not head of list\n";
      exit(0);
   }
#endif
   //AdjIt ait(G);
   itn1=P.last();
   xm1=P[itn1];  
   //cout << "AbsorbPath " << "["<< u->id() << "," << v->id() << "]" << endl;
   //cout << "Length is " << P.length() << endl;
   //Iterate though the list until xm1 is v
   while(itn1 != nil && (xm1=P[itn1]) != v ) {
      //cout << "ignoring" << xm1->id() << endl;
      itn1 = P.pred(itn1);// itn1--;
   }
   if (itn1 == nil)
      return;
   xp1=NULL; //The previous node in the list
   //cout << "Found " << xm1->id() << endl;
   //process the list Pw until u is reached;
   while(xm1 != u && xm1 != NULL) { // must stop if only w in P list
      xi=xm1;
      itn2=itn1;
      itn1 = P.pred(itn1);
      if (itn1 == nil || xi == u) { // u is set after while statement
         break;
      }
      xm1=P[itn1];
#ifndef TRIM
      if (xm1 == NULL){ // redundant check
         cout << "node" << u->id() << "not in list \n";
	 exit(0);
      }
#endif
      //cout << "contracting xm1 = " << xm1->id() << " xi=" << xi->id() << endl;
      //cout << "xi " << xi->id() <<" has " << G.degree(xi) << "edges" << endl;
      //forall_inout_edges(e,xi) 
      //   z = G.opposite(xi,e);//by differentiating between in and out edges this
      
      for(int dinout=0;dinout==0;dinout++)
      for(e=First_Inout_Edge(xi,dinout);e!=nil;) {
         nxte=Succ_Inout_Edge(e,xi,dinout);
         if (G.is_hidden(e)) {
            cout << " hidden edge being processed\n";
            exit(1);

         }
         z = G.opposite(xi,e);//by differentiating between in and out edges this
         //cout << "Processing" << z->id() <<"-" << xi->id() << "->" << e->id() << endl;
         //Hide the edge if it is part of the list of the back edge.
	 if ( z == xm1 /*||  z == xp1 */ || z==x0) { //Shouldn't need to remove xp1
            //cout << "      removing" << "z" << z->id() << ":" << e->id() <<"[" << source(e)->id() <<"-" << target(e)->id() <<"]" << endl;
            //G.del_edge(e);
#ifndef TRIM
            if(G.is_hidden(e)) {
               cout << "Attempt to hide hidden edge\n";
               exit(1);
            }
#endif
            //Rather than deleting the back edge make it a self loop so that the
            //next edge can be found still
            G.hide_edge(e);
#ifdef DISP
            gwpt->update_graph();
#endif
	 } else {
            //cout << "      Moving" << xi->id() << "- " << z->id() << "to " << xi->id() << "-" << x0->id() << endl;
            if(source(e) == target(e)) {
               cout << " attempting to move self loop3\n";
               exit(0);
            }
            G.move_edge(e,x0,z);
	 } 
         e=nxte;
         xp1=xi;
      }     
      //cout << "sigma" << x0->id() << " length="<< sigma[x0].length() << endl;
      sigma[x0].conc(sigma[xi]); 
      //cout << "Added to sigma" << x0->id() << " length="<< sigma[x0].length() << ":=";
      //node n; forall(n,sigma[x0]) cout <<n->id() <<" "; cout << endl;
      P.del_item(itn2); // remove xi from list.
   }

   //cout << "Finished   Absorbing Path"  << endl;
} //ApsorbPath

//Splits the graph into biconnected components
int split_graph(graph &G, node_array<int> components,
             list<edge>& bridges, array<path>& sigma, list<edge>& deg1edges) {
   int num_components=0;
   edge_array<int> ecomp(G,-1);
   edge e;
   node n;
   num_components = BICONNECTED_COMPONENTS(G, ecomp);
   cout << " Number of vertex Biconnected components =" << num_components << endl;
   int A[num_components];
   //sigmaB.resize(num_components);
   array<epath> sigmaB(num_components);
   for(int i=0;i<num_components;i++)
      A[i]=0;
   //Find the size of each component
   forall_edges(e,G) {
      A[ecomp[e]]+=1;
   }

   //The following is a fairly inefficient implementation of 2-edge connectiviy based
   //on 2-vertex connectivity, which is used to first locate bridges and then after
   //removing these bridges the connected components are then returned in sigma
   // Bridges are in components of size 1
   forall_edges(e,G) {
       //cout << e->id() <<"[" << source(e)->id() <<"-" << target(e)->id() <<"] comp ="
       //     << ecomp[e] << "size="<< A[ecomp[e]] <<endl;
      if (A[ecomp[e]] <=1) {
         // All nodes on the edges being the only edge in the components are bridges
         //cout << "bridge found\n";
         bridges.push(e);
      } else { 
        //Add node to a list of nodes for this component
        sigmaB[ecomp[e]].append(e);
      }
   }
   cout << " Num Bridges " << bridges.length() << endl;
   if (!bridges.empty()) {
      //G.hide_edge(bridges.head());
      cout << "Removing " << bridges.length() << " bridges\n";
      forall(e, bridges) {
         // Initally remove these edges
         // Consider later restoring them
         if (G.degree(source(e)) <= 2 && G.degree(target(e)) <= 2) {
            cout << "Questionable edge removal for edge" << e->id() << endl;
         }
#ifndef TRIM
         if(G.is_hidden(e)) {
            cout << "Attempt to hide hidden edge\n";
            exit(1);
         }
#endif
         cout << "Removing Bridge " << source(e)->id() << "-" << target(e)->id() 
              << " [" <<e->id() << "]" << endl;
         G.hide_edge(e); // G.del_edge(e);
      }

      //Strip out and degree one vertices
      bool haspendent=false;
      do {
         haspendent=false;
         forall_nodes(n,G) {
            if(G.degree(n) == 1) {
               e = G.first_adj_edge(n);
               if(!G.is_hidden(e)) {
                  deg1edges.push(e);
                  G.hide_edge(e);
                  haspendent=true;
                  cout << "found pendant edge\n";
               }
            }
         }
      } while(haspendent);
#if 1
      if (! Is_Connected(G)) {
         cout << "Graph is nolonger connected after removing bridges\n";
      }
#endif
      num_components = COMPONENTS(G, components);
      int col=-1;
      sigma.resize(num_components);
      forall_nodes(n, G) {
	 col = components[n];
	 sigma[col].append(n); 
      }
   } else {
      sigma.resize(1);
      sigma[0] = G.all_nodes();
      num_components=1;
   }
   return num_components;
} // split_graph

//Splits the graph into biconnected components
int split_graph_onV(graph &G, node_array<int> components, 
             list<edge>& bridgesA, list<edge>& bridgesB, array<path>&sigma) {
   int num_components=0;
   edge_array<int> ecomp(G,-1);
   edge e;
   node n;
   num_components = BICONNECTED_COMPONENTS(G, ecomp);
   cout << " Number of vertex Biconnected components =" << num_components << endl;
   //Asynmtitically this cost |E| so it is not the best way to do this but in a hurry so REDO LATER
   // the proper solution is to rewrite BICONECTED so that it returns the
   // articulation points as well
   //bool isArtiulation = false;
   list<edge> comp1, comp2;
   forall_nodes(n,G) {
      if ((e = G.first_adj_edge(n)) == NULL) continue;
      comp1.clear() ;comp2.clear();
      int e1comp = ecomp[G.first_adj_edge(n)];
      //forall_adj_edges(e,n) { //LEDA51 seems to have a problem here
      forall_inout_edges(e,n) { //Preemptive fix may cause bug !!
         if (G.is_hidden(e)) continue;
         if(ecomp[e] == e1comp) {
           comp1.push(e);
	 } else {
	   comp2.push(e);
	 }
      }
      if(!comp2.empty()) {
        cout << "Splitting on vertex " << n->id() << endl;
	bridgesA.conc(comp1);
	bridgesB.conc(comp2);
        break;
      }
   }
   if (bridgesA.empty() ) return 0;
   if (!bridgesA.empty()) {
      cout << "Removing for partA " << bridgesA.length() << " bridges\n";
      cout << "Removing for partB " << bridgesB.length() << " bridges\n";
      forall(e, bridgesA) {
         // Initally remove these edges
         // Consider later restoring them
         if (G.degree(source(e)) <= 2 && G.degree(target(e)) <= 2) {
            cout << "Questionable edge removal for edge" << e->id() << endl;
         }
#ifndef TRIM
         if(G.is_hidden(e)) {
            cout << "Attempt to hide hidden edge\n";
            exit(1);
         }
         cout << "Removing Bridge " << e->id() << endl;
#endif
         G.hide_edge(e); // G.del_edge(e);
      }

      //Strip out and degree one vertices
      bool haspendent=false;
      do {
         haspendent=false;
         forall_nodes(n,G) {
            if(G.degree(n) == 1) {
               e = G.first_adj_edge(n);
               if(!G.is_hidden(e)) {
                  //deg1edges.push(e);
                  G.hide_edge(e);
                  haspendent=true;
                  cout << "found pendant edge\n";
               }
            }
         }
      } while(haspendent);
#if 1
      if (! Is_Connected(G)) {
         cout << "Graph is nolonger connected after removing bridges\n";
      }
#endif
      num_components = COMPONENTS(G, components);
      int col=-1;
      sigma.resize(num_components);
      for(int i =0;i< num_components; i++) {
         sigma[i].clear();
      }
      forall_nodes(n, G) {
	 col = components[n];
	 sigma[col].append(n); 
      }
   } else {
      sigma.resize(1);
      sigma[0] = G.all_nodes();
      num_components=1;
   }
   return num_components;
} // splitonV_graph

int main(int argc,char **argv)
{  

   graph G;
   array<path> sigma;
   //string fname="50v_225edges_5c.dim";
#if 1

    string fname;
    if(argc >=2) {
       fname = string(argv[1]);
    }

   
   //string fname="50v_225edges_5c.dim";
   //string fname="50v_10c_18ed.dim";
   //string fname="sh2-3_747v_5081.dim";
   //string fname="comp0sh2-3_747v_5081.dim";
   //fname="globin5.dim";
   //string fname="globin3_742v_3774e.dim";
   //string fname="comp5";
   //string fname="globin3_even_261v_874e.dim";
   ifstream in(fname);
   if(in.fail()) {
      cout << "Unable to open" << fname  << endl;
      exit(0);
   } else {
      if(read_dim(G,in)!=1) {
         cout << "Error reading " << fname  << endl;
         exit(0);
      }
   }
#else
   //string fname="tr1.gw";
   string fname="tr5.gw";
   //string fname="c5.gw";
   if(G.read(fname)!=0) {
      cout << "Unable to open tri.gw" << endl;
      exit(0);
   }
   list<edge> el;
   //Make_Biconnected(G,el); //For tr1 only !!!
#endif
   cout << "Processing Graph file>" << fname << endl;
   G.make_undirected();
   Make_Simple(G);
   cout << "Number of nodes=" << G.number_of_nodes() << endl;
   cout << "Number of edges=" << G.number_of_edges() << endl;

   Delete_Loops(G);
   node n;
   edge e;
   int numdeg2=0;
   int numdeg1=0;
   forall_nodes(n,G) {
      if(G.degree(n) <= 1) {
         numdeg1++;
         cout << "Node " <<n->id() << "is deg less than 2\n";
      }
      if(G.degree(n) == 2) {
         numdeg2++;
         e=G.first_adj_edge(n);
         //G.hide_edge(e);
         e=G.last_adj_edge(n);
         // Uncomment to remove degree 2 edges.
         //G.hide_edge(e);
         //G.hide_node(n);
         //cout << "Node " <<n->id() << "is deg 2\n";
      }
   }
   //Appends inserted edges to el;
   if(!Is_Connected(G)) {
      cout <<"Graph disconnected\n";
      //Make_Connected(G,el);
      //exit(0);
   }
   cout << "Initial number of small <2 deg nodes" << numdeg2 << endl;
   cout << "Initial number of small <1 deg nodes" << numdeg1 << endl;

   list<edge> cut_edges;
   list<edge> bridges;
   list<edge> deg1edges;  // edges of degree 1 after removing bridges.
                          // These edges would have been adjacent to
                          // bridges with one vertex of degree 2
   int num3comp;

   num3comp = TRICONNECTED_COMPONENTS(G, cut_edges, bridges, sigma, deg1edges);

   cout << "number of 3-edge-connect components : " << num3comp  << endl;
   cout << "number of bridges	: " << bridges.length()  << endl;
   cout << "number of cut-edges : " << cut_edges.length()  << endl;
   cout << "number of deg1-postbridge-edges     : " << deg1edges.length()  << endl;
   cout << "number of non deg2 components       : " << (num3comp - numdeg2) << endl;

   //cout << "expectedmax cut-edges" << (num3comp - numdeg2)*(num3comp - numdeg2 -1) << endl;
#ifdef DISP2
   GraphWin gw2(G,"Triconnected Search");
   //label the edges to be deleted blue
   forall_edges(e,G) {
      gw2.set_color(e,black);
      gw2.set_width(e,1);
   }
   forall(e,cut_edges) {
      gw2.set_color(e,blue);
      gw2.set_width(e,1);
   }
   //Thin the graph by deleting edge of degree 2
   //forall_nodes(n,G) {
   //   if(G.degree(n) <= 1) {
   //      G.hide_node(n);
   //   }
   //}
   gw2.set_directed(false);
   gw2.set_node_label_type(user_label);
   gw2.set_node_width(5);
   gw2.update_graph();
   gw2.display();
   gw2.edit();
#endif
#if 1
   //test for degree one vertices
   /*
   forall_nodes(n,G) {
      if(G.degree(n) == 1) {
         e = G.first_adj_edge(n);
         cout << "Found pendant edge id=" << e->id() << endl;
      }
   }
   */
   //bridges = 0;
   int nsafecutedges=0;
   int nsafebridges=0;

   forall(e,bridges) {
      cout << "bridge >" << source(e)->id() << "-" << target(e)->id() << endl ;
      if (G.degree(source(e)) > 2 || G.degree(target(e)) > 2) {
         nsafebridges++;
         //G.del_edge(e);
         if (!G.is_hidden(e)) {
            G.hide_edge(e);
         } else {
           ;//cout << "WARNING bridge edge was not hidden";
         }
      } else { 
         cout << " not bridge degrees " << G.degree(target(e)) 
              << ":" << G.degree(source(e)) <<  endl;
      }
   }
   cout << "Ammended number of bridges : " << nsafebridges<< endl;

   forall(e,cut_edges) {
      //cout << "cut_edge " << source(e)->id() << "-" << target(e)->id() << endl;
      if (!G.is_hidden(e)) {
         // Change to exclude degree 2 edges
         if ( G.degree(source(e)) > 2 || G.degree(target(e)) > 2) {
            nsafecutedges++;
            //G.del_edge(e);
            //cout << "cut-edge degrees " << G.degree(target(e)) 
            //     << ":" << G.degree(source(e)) << endl;
            G.hide_edge(e);
         } else { 
            //cout << "cut-edge degrees " << G.degree(target(e)) 
            //     << ":" << G.degree(source(e)) << "ignored" << endl;
         }
      } else { 
         //cout << "Hidden edges not restored ";
         //cout << "cut-edge degrees " << G.degree(target(e)) 
         //     << ":" << G.degree(source(e)) << endl;
      }
   }
   cout << "Ammended number of cutedges : " << nsafecutedges<< endl;

   list<edge> bridgesA;
   list<edge> bridgesB;
   node_array<int> compArr(G,-1);
   array<path> sigmaV;
   int num2vcomp=0;

   //Potential memory problem by if we reuse simga as the old paths
   // will not be cleared;
   if( !Is_Biconnected(G) ) {
        num2vcomp = split_graph_onV(G, compArr, bridgesA, bridgesB, sigma) ;
        cout << "Found " << num2vcomp << "components after spiting on vertex\n";
   }
   if (num2vcomp > num3comp) num3comp=num2vcomp;
   // Divide the graph up into subgraphs of connected components and write them each to a file
   // prefixed with comp
   int compsize,ttlcompsize=0;
   cout << "component sizes "  << endl;
   for(int i=0; i < num3comp; i++) {
      GRAPH<node,edge> H;
      list<node> &HV = sigma[i];
      CopyInducedGraph(H,G,HV);
      compsize= H.number_of_nodes();
      cout << compsize <<", ";
      if(compsize > 1) {
         ttlcompsize+=compsize;
         string compfname(string("comp%d",i)+fname);
         ofstream out(compfname);

         if(out.fail()) {
            cout << "Unable to open " << compfname  << endl;
            exit(0);
         } else {
            write_dim(H,out) ;
         }
      }
   }
   cout << endl;
#ifdef DISP2
   gw2.update_graph();
   ContinueButton(gw2);
   gw2.edit();
#endif   
#ifdef DISP2_0
   //G.restore_all_edges();
   forall_edges(e,G) {
      gw2.set_width(e,1);
   }
   forall(e,cut_edges) {
      gw2.set_color(e,blue);
      gw2.set_width(e,0);
   }
   gw2.update_graph();
   ContinueButton(gw2);
   gw2.edit();
#endif   
#endif
/*
   forall_nodes(n,G) {
      cout << "Sigma" << n->id() << " length="<< sigma[n].length() << endl;
   }
*/
cout << "Done\n";
   cout << "Number of degree 2 nodes = " << numdeg2 << endl;
   cout << "Number of nodes in subgraphs = " << ttlcompsize << endl;
   return 0; 
}

void write_dim(GRAPH<node,edge> &G, ostream& out)
{
   out << G.number_of_nodes() << " " << G.number_of_edges() << endl;
   edge e;
   forall_edges(e,G) {
      out << source(e)->id() << " " << target(e)->id() << endl;
   }
}
void write_dim(graph &G, ostream& out)
{
   out << G.number_of_nodes() << " " << G.number_of_edges() << endl;
   edge e;
   forall_edges(e,G) {
      out << source(e)->id() << " " << target(e)->id() << endl;
   }
}

//See LEDA _g_inout.c for other graph reading methods
int read_dim(graph &G, istream& in)
{
  int n,i,v,w;
  int s;

  G.clear();
  in >> n;  //number of nodes
  in >> s;  //number of edges
  cout << string("Number of Nodes= %d, Number of Edges = %d",n,s) << endl;
  read_line(in);

  node* AA = new node[n+1];

  G.set_node_bound(n);
  //no node info just number of nodes and number of edges
  for (i=0; i<n; i++) {
//     AA[i] = G.new_node();
       AA[i] = G.new_node();
  }

  G.set_edge_bound(s);

  for (i=1; i<=s; i++) {
        in >> v >> w;
        //DLOGGER(debug,string("%d-%d",v,w),"");
        G.new_edge(AA[v],AA[w]);
  }
  delete[] AA;
  return 1;
}

void print_lists(path const & Pw, path const &Pu) {
   node x;
   cout << "Pu:=" ;
   forall(x,Pu)
      cout << x->id() <<"-";
   cout << endl;
   cout << "Pw:=" ;
   forall(x,Pw)
      cout << x->id() <<"-";
   cout << endl;
}


//Makes H the graph induced by the vertices in G.
void CopyInducedGraph(GRAPH<node,edge>& H, const graph& G, const list<node>& V)
{ // constructs a copy of the subgraph (V,E) of G
  // predondition: E is a subset of VxV
  H.clear();
  //cout << "Copying G. G has " << G.number_of_edges() << "edges\n";
  H.set_node_bound(G.number_of_nodes());
  H.set_edge_bound(G.number_of_edges());
  if (G.is_undirected()) {
     H.make_undirected();
  }
  node_array<node> v_in_H(G,nil);
  node v,x;
  forall(v,V) v_in_H[v] = H.new_node(v);
  edge e;
  node_array<int> Na(G,-1);
  //edge_array<int> Ea(G,-1);
  forall(v,V) {
     forall_adj_edges(e,v) {
        if (G.is_hidden(e)) continue;
        //if( Ea[e] >0) continue;
        //Ea[e] = 1;
        x = G.opposite(v,e);
        //if the adj node is in V
        if(v_in_H[x] != nil ) {
           //Warning aviod double dip!
           //Ie processing each edge twice
           if (Na[x] > 0) continue;
           node s = v_in_H[x];
           node t = v_in_H[v];
           H.new_edge(s,t,e);
        }
     }
     Na[v] = 1;
  }
}

