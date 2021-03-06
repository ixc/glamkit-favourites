from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from .models import FavouritesList, FavouriteItem
from .forms import FavouritesListForm
from .settings import settings as favourites_settings


@login_required
def my_lists(request):
    """
    Redirect to my lists page (need a login to find out which user I am).
    """
    return HttpResponseRedirect(reverse('favourites.lists', args=(request.user.username, )))
    
def favourites_lists(request, username):
    """
    GET:
    Show the user's lists.
    Else 404.
    """
    user = get_object_or_404(User, username=username)

    context = RequestContext(request)
    context['owner'] = user

    #rest is done in template tags
    return render_to_response('favourites/lists.html', context)

def favourites_list(request, list_pk):
    """
    GET:
    Show the given list (if allowed).
    """
    
    lst = get_object_or_404(FavouritesList, pk=list_pk)
    
    if not lst.can_user_view(request.user):
        if favourites_settings['FAVOURITES_REDIRECT_IF_NO_PERMISSION']:
            return HttpResponseRedirect(favourites_settings['FAVOURITES_REDIRECT_IF_NO_PERMISSION'])
        else:
            raise Http404
        
    context = RequestContext(request)
    context['list'] = lst
    
    return render_to_response('favourites/list.html', context)

def create_favourites_list(request, username):
    """
    POST:
    create an empty list (that can hold anything).
    Redirects to referrer, (or list) if no referrer.
    """
    user = get_object_or_404(User, username=username)
    
    if not FavouritesList.can_user_add_list_for_other_user(user=request.user, other_user=user):
        return HttpResponseForbidden()
        
    lst = FavouritesList.objects.create(creator=user)
    
    messages.add_message(request, messages.SUCCESS, '\'%s\' was created successfully.' % lst.title)

    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except KeyError:
        return HttpResponseRedirect(lst.get_absolute_url())

@login_required
def create_favourites_item(request):
    """
    POST:
    Takes parameters: content_type_id, object_id, list (id)
    add an item to a list. If list is unspecified, create a new list.
    """

    try:
        list_id = int(request.POST.get('list_id'))
    except (ValueError, TypeError):
        list_id = None
    
    if list_id is None:
        messages.add_message(request, messages.ERROR, 'Please choose a list to add to.')
        try:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        except KeyError:
            raise Http404
            
    content_type_id = int(request.POST['content_type_id'])
    object_id = int(request.POST['object_id'])
    item = get_object_or_404(ContentType.objects.get_for_id(content_type_id).model_class(), id=object_id)

    if list_id < 0:
        lst = FavouritesList.objects.create_from_item(creator=request.user, item=item)
        messages.add_message(request, messages.SUCCESS, '\'%s\' was created, and \'%s\' was added to it.' % (lst, item))
    else:
        lst = get_object_or_404(FavouritesList, pk=list_id)
        if lst.can_user_add_item(request.user):
            lst.add_item(item=item, added_by=request.user)
            messages.add_message(request, messages.SUCCESS, '\'%s\' was added to \'%s\'.' % (item, lst))
        else:
            return HttpResponseForbidden()
            
    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except KeyError:
        return HttpResponseRedirect(lst.get_absolute_url())

@login_required
def delete_favourites_item(request, list_pk, item_pk):
    item = get_object_or_404(FavouriteItem, collection__id=list_pk, pk=item_pk)
    lst = item.collection
    if not item.can_user_delete(request.user):
        return HttpResponseForbidden()

    s = unicode(item.item)
    item.delete()
    messages.add_message(request, messages.SUCCESS, '\'%s\' was removed from \'%s\'.' % (s, lst))
    return HttpResponseRedirect(lst.get_absolute_url())

        
@login_required
def edit_favourites_list(request, list_pk):
    lst = get_object_or_404(FavouritesList, pk=list_pk)
    if not lst.can_user_edit(request.user):
        raise Http404
    
    if request.POST:
        form = FavouritesListForm(request.POST, instance=lst)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(lst.get_absolute_url())
    else:        
        form = FavouritesListForm(instance = lst)
    
    context = RequestContext(request)
    context['form'] = form
    context['list'] = lst
    return render_to_response("favourites/edit_list.html", context)

@login_required
def delete_favourites_list(request, list_pk):
    lst = FavouritesList.objects.get(id=list_pk)
    
    if not lst.can_user_delete(request.user):
        return HttpResponseForbidden()
        
    lst.delete()
    messages.add_message(request, messages.SUCCESS, '\'%s\' was deleted successfully.' % (lst,))
    return HttpResponseRedirect(reverse('favourites.my_lists'))