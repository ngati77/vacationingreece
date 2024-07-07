from django.shortcuts import render,  get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Comment, Phrase, Subscribed
from .forms import PostForm, CommentForm, PhraseForm, SubscribedForm
#from tours.tour_emails import tour_emails
from django.conf import settings
from django.template.loader import render_to_string

from .decorators import check_recaptcha

from django.contrib.auth.decorators import login_required, user_passes_test

''' Check if user has permition to edit blog'''
def group_required(*group_names):
   """Requires user membership in at least one of the groups passed in."""

   def in_groups(u):
       if u.is_authenticated:
           if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
               return True
       return False
   return user_passes_test(in_groups)

def post_list(request):
    meta_des  = "Vacation In Greece blog"
    meta_key = "Vacation in greece"
    title        = 'Latest Posts'
    posts = Post.objects.filter(published_date__lte=timezone.now(),type='p').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': [posts[0::2], posts[1::2]],
                                                    'page_title':   title,
                                                    'meta_des':     meta_des,
                                                    'meta_key':     meta_key,
                                                    'title':        title,
                                                    })

def post_detail(request, url):
    post = get_object_or_404(Post, url=url)
    meta_des  = f"Vacation in Greece post {post.title}"
    meta_key  = meta_des
    title        = post.title
    return render(request, 'blog/post_detail.html', {'post': post, 
                                                    'page_title':   title,
                                                    'meta_des':     meta_des,
                                                    'meta_key':     meta_key,
                                                    'title':        title,
                                                    'ShowComments':True})

@login_required
# The way to use this decorator is:
@group_required('blog_admin')
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            #post.published_date = timezone.now()
            post.save()
            return redirect('blog:post_detail', url=post.url)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
@group_required('blog_admin')
def phrase_new(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = PhraseForm(request.POST, request.FILES)
        if form.is_valid():
            phrase = form.save(commit=False)
            phrase.post = post
            phrase.save()
            return redirect('blog:post_detail', url=post.url)
    else:
        next_order = post.get_next_pharse_number()
        form = PhraseForm(initial={'order': next_order})
    return render(request, 'blog/phrase_edit.html', {'form': form})

@login_required
@group_required('blog_admin')
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            #post.published_date = timezone.now()
            post.save()
            return redirect('blog:post_detail', url=post.url)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
@group_required('blog_admin')
def phrase_edit(request, pk):
    phrase = get_object_or_404(Phrase, pk=pk)
    if request.method == "POST":
        form = PhraseForm(request.POST, request.FILES,instance=phrase)
        if form.is_valid():
            phrase = form.save(commit=False)
            phrase.save()
            return redirect('blog:post_detail', url=phrase.post.url)
    else:
        form = PhraseForm(instance=phrase)
    return render(request, 'blog/phrase_edit.html', {'form': form})

@login_required
@group_required('blog_admin')
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    title = 'טיוטות'
    return render(request, 'blog/post_list.html', {'posts': [posts[0::2], posts[1::2]],
                                                   'page_title':    title,
                                                    'title':        title,
                                                   })

def send_email_thank_you(subscribed):
    ''' New subscribed, sends email
    '''
    post = Post.objects.filter(published_date__lte=timezone.now(),type='p').order_by('-published_date')[0]
    title   = "Thanks for suscribed "
    msg_plain =  "New Post "

    
    to=[subscribed.email]
    msg_html = render_to_string('emails/new_post.html',{'post':post, 'subscribed':subscribed })
    #print(msg_html)
    #emailTitle = "   "
    #tour_emails.send_email(to=to,
    #                    msg_html=msg_html, 
    #                    msg_plain=msg_plain, 
    #                    cc=settings.BCC_EMAIL, 
    #                    title=title)


def send_new_publish_post(post):
    ''' Send email to subscribed list
    '''
    subList = Subscribed.objects.filter(confirmed=True)
    title   = post.title
    msg_plain =  " New Post"

    for subscribed in subList:
        to=[subscribed.email]
        msg_html = render_to_string('emails/new_post.html',{'post':post, 'subscribed':subscribed })
        #print(msg_html)
    #emailTitle = "New Post "
        #tour_emails.send_email(to=to,
        #                    msg_html=msg_html, 
        #                    msg_plain=msg_plain, 
        #                    cc=settings.BCC_EMAIL, 
        #                    title=title)

@login_required
@group_required('blog_admin')
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    send_new_publish_post(post)
    return redirect('blog:post_detail', url=post.url)

@login_required
@group_required('blog_admin')
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('blog:post_list')

def post_writers(request):
    posts = Post.objects.filter(published_date__isnull=False,type='w').order_by('created_date')
    meta_des  = "Vacation In Greece the writers"
    meta_key  = "writers"
    title        = 'About Us'
    return render(request, 'blog/post_detail.html', {'post': posts[0],
                                                    'page_title':title,
                                                    'meta_des':  meta_des,
                                                    'meta_key':  meta_key,
                                                    'title':     title,
                                                    'ShowComments':False})

    # return render(request, 'blog/post_list.html', {'posts': [posts[0],'page_title':'קצת עלינו'})


def inform_admin(comment_to_post, comment):
    to=[settings.EMAIL_GMAIL_YAEL]
    
    msg_html = render_to_string('emails/email_admin.html',{'comment_to_post':comment_to_post,'comment':comment})
    msg_plain =  "Check Blog"
    title     = 'New Comment'
    #emailTitle = " New Comment  "
    #tour_emails.send_email(to=to,
    #                        msg_html=msg_html, 
    #                        msg_plain=msg_plain, 
    #                        cc=settings.BCC_EMAIL, 
    #                        title=title)

'''
def send_email(task, obj):
    to=[settings.EMAIL_GMAIL_YAEL]
    if obj.email:
        to.append(obj.email)
    if task == 'Check':
        msg_html = ""
        msg_plain =  "New Comment"
        emailTitle = " New Comment  "
        to=settings.BCC_EMAIL
    if task=='New comment':
        msg_html = render_to_string('emails/email_new_comment.html', {'comment':obj})
        msg_plain = str(obj.id) + " New Comment "
        emailTitle = "Thanks for writing us  "
    elif task = 'New Subscribed':
        msg_html = render_to_string('emails/email_new_subscribed.html', {'comment':obj})
        msg_plain = str(obj.id) + "  New user "
        emailTitle = "Thanks for your registration"
    elif task = 'Published comment':
        # A new comment has been published, inform the person who wrote it
        if (obj.post):
            msg_html = render_to_string('emails/email_comment_published.html', {'comment':obj})
            msg_plain =  f"Comment published: {str(obj.id)}"
            emailTitle = " Your comment is now in the website "


        
try:

    #tour_emails.send_email( to=[settings.EMAIL_GMAIL_YAEL],
    #                                msg_html=msg_html, 
    #                                msg_plain=msg_plain, 
    #                                cc=[], 
    #                                title=title)
except:
    print('Got an error...')
'''


@check_recaptcha
def add_comment_to_post(request, url):
    post = get_object_or_404(Post, url=url)
    meta_des  = "Vacation in Greece add comment"
    meta_key  = meta_des
    title        = 'Add comment'
    if request.method == "POST":

        form = CommentForm(request.POST)
        if form.is_valid() and request.recaptcha_is_valid:

            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            inform_admin(True,comment)
            return redirect('blog:post_detail', url=post.url)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form,
                                                             'page_title':title,
                                                             'meta_des':  meta_des,
                                                             'meta_key':  meta_key,
                                                             'title':     title,
                                                             'title':     title,
                                                             'reCAPTCHA_site_key': settings.GOOGLE_RECAPTCHA_PUBLIC_KEY
                                                                })
@check_recaptcha
def add_comment_to_comment(request, PostUrl, CommentPk):
    commentParent = get_object_or_404(Comment, pk=CommentPk)
    title        = ' Add comment'
    meta_des  = "Vacation in Greece add comment"
    meta_key  = "add comment"
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid() and request.recaptcha_is_valid:

            comment = form.save(commit=False)
            comment.commentParent = commentParent
            comment.save()
            inform_admin(False, comment)

            return redirect('blog:post_detail', url=PostUrl)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form,
                                                             'page_title':title,
                                                             'meta_des':  meta_des,
                                                             'meta_key':  meta_key,
                                                             'title':     title,
                                                             'reCAPTCHA_site_key': settings.GOOGLE_RECAPTCHA_PUBLIC_KEY
                                                              })
 
def subscribed_success(request):
    meta_des = "Registeration to our distribution list has successed"
    meta_key = "Registration successed "
    title = meta_key 
    
    return render(request, 'blog/subscribed_success.html',{'page_title':title,
                                                             'meta_des':  meta_des,
                                                             'meta_key':  meta_key,
                                                             'title':     title,
    
    })


def subscribed_view(request):
    meta_des  = "suscribed "
    meta_key  = "add suscribed"
    title = "Send me email when new post is published"
    if request.method == "POST":
        form = SubscribedForm(request.POST)
        if form.is_valid():
            subscribed = form.save(commit=False)
            subscribed.save()
            send_email_thank_you(subscribed)
            return redirect('blog:subscribed_success')
    else:
        form = SubscribedForm()
    return render(request, 'blog/subscribed.html', {'form': form,
                                                    'page_title':title,
                                                    'meta_des':  meta_des,
                                                    'meta_key':  meta_key,
                                                    'title':     title,
    })

@login_required
@group_required('blog_admin')
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    # If this is not null then it point to a post
    if (comment.post):
        return redirect('blog:post_detail', url=comment.post.url)
    else:
        return redirect('blog:post_detail', url=comment.commentParent.post.url)

@login_required
@group_required('blog_admin')
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('blog:post_detail', url=comment.post.url)
