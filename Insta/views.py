# from django.shortcuts import render
from annoying.decorators import ajax_request
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy

from Insta.models import Post, Like, InstaUser, UserConnection, Comment

from django.contrib.auth.mixins import LoginRequiredMixin

# from django.contrib.auth.forms import UserCreationForm
from Insta.forms import CustomUserCreationForm

# from rest_framework import generics
# from .serializers import PostSerializer
# Create your views here.

class HelloWorld(TemplateView):
	template_name = 'test.html'


class PostsView(LoginRequiredMixin, ListView):
	model = Post
	template_name = 'index.html'
	login_url = 'login'

	def get_queryset(self):
		current_user = self.request.user
		following = set()
		for conn in UserConnection.objects.filter(creator=current_user).select_related('following'):
			following.add(conn.following)
		return Post.objects.filter(author__in=following).order_by('-posted_on')

class PostDetailView(DetailView):
	model = Post
	template_name = 'post_detail.html'

	def get_context_data(self, **kwargs):
		data = super().get_context_data(**kwargs)
		liked = Like.objects.filter(post=self.kwargs.get('pk'), user=self.request.user).first()
		if liked:
			data['liked'] = 1
		else:
			data['liked'] = 0
		return data

class ExploreView(LoginRequiredMixin, ListView):
	model = Post
	template_name = 'explore.html'
	login_url = 'login'

	def get_queryset(self):
		return Post.objects.all().order_by('-posted_on')[:10]


class UserDetailView(LoginRequiredMixin, DetailView):
	model = InstaUser
	template_name = 'user_detail.html'
	login_url = 'login'


class UserUpdateView(LoginRequiredMixin, UpdateView):
	model = InstaUser
	template_name = 'user_update.html'
	fields = ['profile_pic', 'username']
	login_url = 'login'
	# success_url = reverse_lazy("user_detail", model.pk)

class PostCreateView(LoginRequiredMixin, CreateView):
	model = Post
	template_name = 'post_create.html'
	# fields = '__all__'
	fields = ['title', 'image']

	def form_valid(self, form):
        #Add logged-in user as autor of comment THIS IS THE KEY TO THE SOLUTION
		form.instance.author = self.request.user
        # Call super-class form validation behaviour
		return super(PostCreateView, self).form_valid(form)

	login_url = 'login'


class PostUpdateView(UpdateView):
	model = Post
	template_name = 'post_update.html'
	fields = ['title']

class PostDeleteView(DeleteView):
	model = Post
	template_name = 'post_delete.html'
	success_url = reverse_lazy("posts")

class SignUp(CreateView):
	form_class = CustomUserCreationForm
	template_name = 'signup.html'
	success_url = reverse_lazy("login")

# class PostAPIView(generics.ListAPIView):
# 	queryset = Post.objects.all()
# 	serializer_class = PostSerializer


@ajax_request
def addLike(request):
    post_pk = request.POST.get('post_pk')
    post = Post.objects.get(pk=post_pk)
    try:
        like = Like(post=post, user=request.user)
        like.save()
        result = 1
    except Exception as e:
        like = Like.objects.get(post=post, user=request.user)
        like.delete()
        result = 0

    return {
        'result': result,
        'post_pk': post_pk
    }


@ajax_request
def addComment(request):
	comment_text = request.POST.get('comment_text')
	post_pk = request.POST.get('post_pk')
	post = Post.objects.get(pk=post_pk)
	comment_info = {}

	try:
		comment = Comment(comment=comment_text, user=request.user, post=post)
		comment.save()
		username = request.user.username
		commenter_info = {
			'username': username,
			'comment_text': comment_text
		}
		result = 1
	except Exception as e:
		print(e)
		result = 0
	
	return {
		'result': result,
		'post_pk': post_pk,
		'commenter_info': commenter_info
	}


@ajax_request
def toggleFollow(request):
	current_user = InstaUser.objects.get(pk=request.user.pk)
	follow_user_pk = request.POST.get('follow_user_pk')
	follow_user = InstaUser.objects.get(pk=follow_user_pk)

	try:
		if current_user != follow_user:
			if request.POST.get('type') == 'follow':
				connection = UserConnection(creator=current_user, following=follow_user)
				connection.save()
			elif request.POST.get('type') == 'unfollow':
				UserConnection.objects.filter(creator=current_user, following=follow_user).delete()
			result = 1
		else:
			result = 0
	except Exception as e:
		print(e)
		result = 0
	
	return {
		'result': result,
		'type': request.POST.get('type'),
		'follow_user_pk': follow_user_pk
	}
