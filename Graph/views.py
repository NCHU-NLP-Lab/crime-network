from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient

def homepage(request):
	template = get_template('index.html')
	html = template.render()
	return redirect('/graph/')

def graph(request):
    template = get_template('graph.html')
    level = ['第1層', '第2層']
    html = template.render(locals())
    return HttpResponse(html)

@csrf_exempt
def search_prisoner(request):
    print(request.POST)
    prisoner = request.POST['prisoner']

    client = MongoClient('140.120.13.244', 27018)
    Node = list(client.Law.Node.find({}))
    result = []

    for n in Node:
        if(prisoner in n['Name']):
            result.append(n['Name'])

    result = {'prisoner': result}
    return JsonResponse(result)

@csrf_exempt
def get_graph_data(request):
    print(request.POST)
    prisoner = request.POST['prisoner']
    level = request.POST['level']

    global Node, Link, Edge
    Node = [] # Graph node
    Link = [] # Graph edge
    Target = [prisoner] # 現在level要找的node
    haveFindNode = [] # 曾經找過的node
    Edge = {} # 所有node的edge

    for l in range(int(level)): 
        for t in Target:
            get_graph(t)
            haveFindNode.append(t)
        Target = []
        for n in Node: # target為新增的node中 不曾找過的node
            if(n not in haveFindNode): # 曾經找過node 不再是下次target
                Target.append(n)

    Map = []
    for n in Node:
        Map.append({'name': n})

    result = {'Map': Map, 'Link': Link}
    # print(result)

    return JsonResponse(result)

def get_graph(prisoner):

    client = MongoClient('140.120.13.244', 27018)
    if(prisoner not in Edge):
        this_Edge = list( client.Law.Edge.find({'From Name': prisoner}))
        Edge[prisoner] = this_Edge
    else:
        this_Edge = Edge[prisoner]
    prisoner_relate_node = []

    if(prisoner not in Node):
        Node.append(prisoner)
    

    for e in this_Edge:
        if(e['To Name'] not in Node):
            Node.append(e['To Name'])
        prisoner_relate_node.append(e['To Name'])
        # print('e: ', e)
        Link.append({'source': Node.index(e['From Name']), 'target': Node.index(e['To Name']), 'weight': e['Weight']})
    
    for ni in prisoner_relate_node:
        if(ni not in Edge):
            relate_edge = list( client.Law.Edge.find({'From Name': ni}))
            Edge[ni] = relate_edge
        else:
            relate_edge = Edge[ni]
        # print('relate', relate_edge)
        for re in relate_edge:
            for nj in prisoner_relate_node:
                if(re['To Name'] == nj):
                    Link.append({'source': Node.index(re['From Name']), 'target': Node.index(re['To Name']), 'weight': re['Weight']})



        


# Test mongodb
# client = MongoClient('140.120.13.244', 27018)
# Edge = client.Law.Edge
# List = list( Edge.find({'From Name': '許湘湄'}) )
# # for n in List:
# #     if ('楊子丘' == n['Name'] ):
# #         print('YES')
# print(len(List))
# print(List)

# 遞迴作法 probelm: second level preformance low
# def get_graph_data(request):
#     print(request.POST)
#     prisoner = request.POST['prisoner']
#     level = request.POST['level']

#     global Node, Link
#     Node = []
#     Link = []
#     Target = [prisoner] # 現在level要找的node
#     haveFindNode = [] # 曾經找過的node

#     for l in range(int(level)): 
#         for t in Target:
#             get_graph(t)
#             haveFindNode.append(t)
#         Target = []
#         for n in Node: # target為新增的node中 不曾找過的node
#             if(n not in haveFindNode): # 曾經找過node 不再是下次target
#                 Target.append(n)

#     Map = []
#     for n in Node:
#         Map.append({'name': n})

#     result = {'Map': Map, 'Link': Link}
#     # print(result)

#     return JsonResponse(result)

# def get_graph(prisoner):

#     client = MongoClient('140.120.13.244', 27018)
#     Edge = list( client.Law.Edge.find({'From Name': prisoner}))
#     prisoner_relate_node = []

#     if(prisoner not in Node):
#         Node.append(prisoner)
    

#     for e in Edge:
#         if(e['To Name'] not in Node):
#             Node.append(e['To Name'])
#         prisoner_relate_node.append(e['To Name'])
#         # print('e: ', e)
#         Link.append({'source': Node.index(e['From Name']), 'target': Node.index(e['To Name']), 'weight': e['Weight']})
    
#     for ni in prisoner_relate_node:
#         relate_edge = list( client.Law.Edge.find({'From Name': ni}))
#         # print('relate', relate_edge)
#         for re in relate_edge:
#             for nj in prisoner_relate_node:
#                 if(re['To Name'] == nj):
#                     Link.append({'source': Node.index(re['From Name']), 'target': Node.index(re['To Name']), 'weight': re['Weight']})