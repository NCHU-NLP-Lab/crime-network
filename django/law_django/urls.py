"""law_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path
from Graph import views as Graph_views

Graph_patterns = [
    re_path(r"^$", Graph_views.homepage),
    re_path(r"^graph/$", Graph_views.graph),
    re_path(r"^get_graph_data/$", Graph_views.get_graph_data),
    re_path(r"^search_prisoner/$", Graph_views.search_prisoner),
    re_path(r"^get_shortest_path/$", Graph_views.get_shortest_path),
    re_path(r"^get_verdict/$", Graph_views.get_verdict),
]

urlpatterns = [
    path(r"", include(Graph_patterns)),
]
