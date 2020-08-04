import networkx as nx
import numpy as np
from collections import deque
from tqdm.notebook import tqdm

class InfuenceMaximizer:
    """
    Independent Cascade modelにおける影響力が最大であるノードを特定するクラス 
    
    Attributes
    ----------
    network : ndarray[[float, float, float], ...]
        [[from_node, to_node, probability], ...]
    k : int
        kノードで影響力を最大にする
    R : int
        シミュレーション数
    nodes : array of int
        グラフ上のノード集合
    edge_size : int
        original graphの枝数
    G_V_only : nx.Graph
        original graphのノードのみのグラフ
    latest : dict
        latest[index(<R)][node]
        gain計算の高速化に用いるフラグ
    delta : dict
        delta[index(<R)][node]
        nodeを追加することで増加する影響数
    G : dict
        G[index(<R)] : index回目のシミュレーションにより得られるDAGs
    comp : dict
        comp[index of DAG][original node number] -> DAG node number
    A : dict
        A[index(<R)] : index回目のシミュレーションにおいてハブに到達する頂点の集合
    h : dict
        h[i] : index回目のシミュレーションにおいてのハブノード
    D : dict
        D[index(<R)] : index回目のシミュレーションにおいてハブから到達する頂点の集合
    V : dict
        V[index(<R)] : index回目のシミュレーションにより得られるDAGsの頂点集合
    S : list
        影響力を最大にする頂点集合
    run_flag : bool
        runメソッドを実行したかのフラグ
    """
    def __init__(self, network, k, R):
        """
        Parameters
        ----------
        network : ndarray[[float, float, float], ...]
        [[from_node, to_node, probability], ...]
        k : int
            kノードで影響力を最大にする
        R : int
            シミュレーション数
        """
        
        self.network = network
        self.k = k
        self.R = R
        
        self.nodes = np.unique(network[:, :2]).astype(np.int)
        self.edge_size = self.network.shape[0]
        self.G_V_only = nx.DiGraph()
        self.G_V_only.add_nodes_from(self.nodes)
        
        self.latest = dict()
        self.delta = {i:dict() for i in range(self.R)}
        
        self.G = dict()
        self.comp = dict()
        self.A = dict()
        self.h = dict()
        self.D = dict()
        self.V = dict()
        self.S = []
        
        self.run_flag = False
        
    def make_live_edge(self):
        """
        枝確率に従って残った枝を返す
        
        Returns
        -------
        live_edges : array of int
            残った枝のarrya型のindex
        """
        rand = np.random.uniform(0, 1, self.edge_size)
        l = np.where(rand < self.network[:, 2])[0]
        return self.network[l][:, :2].astype(np.int)
        
    def bfs(self, G, S):
        """
        幅優先探索
        
        Parameters
        ----------
        G : nx.DiGraph
            対象のグラフ
        S : array-like
            seed(幅優先探索する最初のノードの集合)
        
        Returns
        -------
        visited : dict
            {visited node: pre-node}
        """
        visited = {s: None for s in S}
        queue = deque(S)
        
        while queue:
            v = queue.popleft()
            out_node = G.successors(v)
            for u in out_node:
                if not (u in visited):
                    queue.append(u)
                    visited[u] = v
        return visited
    
    def bfs_reverse(self, G, S):
        """
        逆グラフにおける幅優先探索
        
        Parameters
        ----------
        G : nx.DiGraph
            対象のグラフ
        S : array-like
            seed(幅優先探索する最初のノードの集合)
            
        Returns
        -------
        visited : dict
            {visited node: pre-node}
        """
        
        visited = {s:None for s in S}
        queue = deque(S)
        while queue:
            v = queue.popleft()
            in_node = G.predecessors(v)
            for u in in_node:
                if not (u in visited):
                    queue.append(u)
                    visited[u] = v
        return visited
    
    def scc(self, G):
        """
        強連結成分分解
        
        Returns
        -------
        group : dict
            {original node number : DAG node number, ...}
        
        dag : nx.DiGraph
            member属性には、集約された頂点数が格納されている
        """
        
        # 行きがけ深さ優先探索
        visited = dict([])
        vs = deque([])
        
        for s in G.nodes():
            if s not in visited:
                visited[s] = None
                stack = deque([s])
                vs_tmp = deque([s])
                
                while stack:
                    v = stack.pop()
                    vs_tmp.appendleft(v)
                    for u in G[v]:
                        if u not in visited:
                            visited[u] = s
                            stack.append(u)
                vs.extendleft(vs_tmp)

        # 帰りがけ深さ優先探索
        group = dict([])
        group_num = 0
        DAG = nx.DiGraph()
        for s in vs:
            if s not in group:
                w = 1
                Stack = deque([s])
                members = []
                while Stack:
                    v = Stack.pop()
                    members.append(v)
                    group[v] = group_num
                    in_node = G.predecessors(v)
                    for u in in_node:
                        if u not in group:
                            group[u] = group_num
                            w += 1
                            Stack.append(u)
                        else:
                            if group_num !=  group[u]:
                                DAG.add_edge(group[u], group_num)
                DAG.add_node(group_num, weight=w, members=members)
                group_num += 1
                
        return group, DAG

    def make_random_DAGs(self):
        """
        - シミュレーションによってランダムグラフを作成
        - 強連結成分分解
        - ハブノードを特定
        - ハブに到達するノード集合を探索
        - ハブから到達するノード集合を探索
        上記をR回行なっている
        """
        
        for i in tqdm(range(self.R)):
            G_ = self.G_V_only.copy()
            G_.add_edges_from(self.make_live_edge())
            
            self.comp[i], self.G[i] = self.scc(G_)
            
            G_i_deg = dict(self.G[i].degree())
            self.h[i] = max(G_i_deg, key=G_i_deg.get)
            self.D[i] = set(self.bfs(self.G[i], [self.h[i]]))
            self.A[i] = set(self.bfs_reverse(self.G[i], [self.h[i]])) - set([self.h[i]])
            self.V[i] = self.G[i].nodes()
            self.latest[i] = {v: False for v in self.V[i]}
            
    def gain(self, i, v_V):
        """
        ノードの影響力の増分を計算する
        
        Parameters
        ----------
        i : int
            何回目のシミュレーションか
        v_V : int
            影響力の増分を計算するノード
        
        Returns
        -------
        latest[i][v] : float
            影響力の増分
        """
        # i回目のシュミレーションにliveしなかった頂点はそもそもgainが0
        if v_V not in self.comp[i]:
            return 0
        
        # v:i回目のシュミレーションで作成されたグラフのv_Vを含む強連結成分
        v = self.comp[i][v_V]
        
        if v not in self.G[i].nodes():
            return 0
        
        # G[i].nodes()にvがない場合0(アップデータにより後に消されていく可能性があるため)
        if v not in self.G[i].nodes():
            self.delta[i][v] = 0
            return 0
        
        # 計算済みのため、そのまま返す
        if self.latest[i][v]:
            return self.delta[i][v]
        
        self.latest[i][v] = True
        
        # len(S)==0の理由は初回のみ行えば良いため(h(ハブ)以降の到達頂点数は一回行えば十分であるため)
        # vがhのacestorだった場合、hの到達頂点数を計算して、他のacestorの時にも使い回す
        if (v in self.A[i]) and (len(self.S) == 0):
            # hのGAINをはじめから足しておく([0]なのは、何を選んでもあるvへ写像されるため)
            h_V = self.G[i].nodes[self.h[i]]["members"][0]
            self.delta[i][v] = self.gain(i, h_V)
        else:
            self.delta[i][v] = 0
            
        # bfs
        Q = deque([v])
        # Xは探索済みの強連結成分
        X = set([v])
        while Q:
            u = Q.popleft()

            if (v in self.A[i]) and (u in self.D[i]) and (len(self.S) == 0):
                continue

            self.delta[i][v] += self.G[i].nodes[u]["weight"]


            Edges = self.G[i].out_edges(u)
            for u_, w in Edges:
                # 探索済みの強連結成分は探索しなくていいので、w not in X
                # w in V[i]はのちのupdateでV[i]が変化するため
                if (w not in X) and (w in self.G[i].nodes()):
                    Q.append(w)
                    X.add(w) 
        return self.delta[i][v]
        
    def update(self, i, t_V):
        """
        探索する必要のないノードをグラフ上から消去する
        
        Parameters
        i : int
            何回目のシミュレーションか
        t_V : int
            t_Vから到達可能な頂点集合を消去する
        ----------
        """
        if t_V not in self.comp[i]:
            return self.G[i]
    
        # t:DAG上でのノードid
        t = self.comp[i][t_V]

        if t in self.G[i]:
            # t -> u
            u = list(self.bfs(self.G[i], [t]))
            # u = list(dict(nx.bfs_edges(G[i], t)))
            # v -> u:上で求めたuにだどりつくvを求める
            v = set(self.bfs_reverse(self.G[i], u))

            # v かつ Viに存在する頂点
            v_ = list(v & set(self.G[i].nodes()))
            self.latest[i].update(zip(v_, [False]*len(v_)))

            self.G[i].remove_nodes_from(u)
        
    def run(self):
        """
        PMCを実行する
        
        Returns
        -------
        S : list
            影響力を最大するノード集合
            
        Example
        -------
        枝確率を計算済みのネットワークを読み込む
        >>> network = pd.read_csv("data.csv").values
        >>> inf = InfuenceMaximizer(network, 1, 100)
        >>> inf.run()
        [0]
        """
        if self.k == 1:
            self.run_flag = True
        
        self.make_random_DAGs()
        print('comp init')
        
        for j in range(self.k):
            self.v_gain = {v: sum([self.gain(i, v) for i in range(self.R)])/self.R
                      for v in tqdm(self.nodes)}
            t = max(self.v_gain, key=self.v_gain.get)
            self.S.append(t)
            
            for i in range(self.R):
                self.update(i, t)
        
        return self.S
    
    def influence_result(self):
        """
        影響力の計算結果を返す
        
        Returns
        -------
        v_gain : dict
            {node : expeted influence, ...,}
        """
        if not self.run_flag:
            tmp = self.k
            self.k = 1
            self.run()
            self.k = tmp
        return self.v_gain