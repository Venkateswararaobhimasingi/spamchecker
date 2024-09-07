from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from django.db.models import Q
from collections import namedtuple
from users.models import Profile
import pickle
import string
import os
from nltk.corpus import stopwords
from nltk.tokenize import TreebankWordTokenizer
from nltk.stem.porter import PorterStemmer
import nltk

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Initialize the Porter Stemmer and tokenizer
ps = PorterStemmer()
tokenizer = TreebankWordTokenizer()

tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))


# Function to preprocess and transform the text
def transform_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Tokenize using TreebankWordTokenizer
    text = tokenizer.tokenize(text)
    
    # Remove non-alphanumeric characters
    y = [i for i in text if i.isalnum()]
    
    # Remove stopwords and punctuation
    y = [i for i in y if i not in stopwords.words('english') and i not in string.punctuation]
    
    # Stem the words
    y = [ps.stem(i) for i in y]
    
    # Return the processed text as a single string
    return " ".join(y)

# Function to check if a message is spam or not
def is_spam(message_content):
    # 1. Preprocess the input text
    transformed_text = transform_text(message_content)
    
    # 2. Vectorize the transformed text
    vector_input = tfidf.transform([transformed_text])
    
    # 3. Predict whether the message is spam or not
    result = model.predict(vector_input)[0]
    
    # Return True if spam, False otherwise
    return result == 1

# View to create and save a message
@login_required
def create(request):
    if request.method == 'POST':
        # Accessing form data from the request directly
        to_address = request.POST.get('to_address')
        subject = request.POST.get('subject')
        message_content = request.POST.get('message_content')

        # Get the email address of the currently logged-in user
        from_address = request.user.email

        # Creating a new Message instance
        message = Message(
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            message_content=message_content,
            author=request.user  # Set the current user as the author
        )

        # Determine if the message is spam or not
        message.is_spam = is_spam(message.message_content)

        # Save the message to the database
        message.save()

        return redirect('list')  # Replace with your redirect target

    return render(request, 'spam/msg.html')


# Create your views here.



@login_required
def display(request, id):
    # Get the current user's email
    user_email = request.user.email

    # Fetch messages where the to_address or from_address matches the current user's email
    messages = Message.objects.filter(to_address=user_email).union(
        Message.objects.filter(from_address=user_email)
    ).order_by('-date_sent')

    # Count unread messages for the current user
    unread_count = Message.objects.filter(
        to_address=user_email,
        is_read=False
    ).count()

    # Fetch the specific message by ID
    message1 = get_object_or_404(Message, id=id)

    # Mark the message as read if it's not already read
    if not message1.is_read:
        message1.is_read = True
        message1.save()

    # Prepare the context dictionary
    context = {
        'message': message1,
        'count': unread_count  # Include the unread message count
    }

    # Render the template with the context containing the message and unread count
    return render(request, 'spam/display.html', context)


@login_required
def list(request):
    # Get the current user's email
    user_email = request.user.email

    # Fetch messages where the to_address or from_address matches the current user's email
    messages = Message.objects.filter(
        to_address=user_email
    ).union(
        Message.objects.filter(from_address=user_email)
    ).order_by('-date_sent')

    # Count unread messages for the current user
    unread_count = Message.objects.filter(
        to_address=user_email,
        is_read=False
    ).count()

    # Prepare profile picture URLs
    profiles = Profile.objects.all()
    profile_pics = {profile.user.email: profile.image.url for profile in profiles}
    
    # Prepare a named tuple to hold message and profile pic information
    MessageWithProfile = namedtuple('MessageWithProfile', ['message', 'profile_pic'])

    # Prepare a list to store the message and profile pic tuples
    messages_with_profile_pics = []
    for message in messages:
        # Determine the profile picture URL
        profile_pic_url = profile_pics.get(message.to_address, '/media/default.jpg')
        
        # Append the tuple to the list
        messages_with_profile_pics.append(MessageWithProfile(message=message, profile_pic=profile_pic_url))

    # Render the template with the context containing messages, profile pics, and unread message count
    return render(request, 'spam/list.html', {
        'messages_with_profile_pics': messages_with_profile_pics,
        'count': unread_count,
    })

@login_required
def check(request):
    spam_check_result = None
    message_content = ''

    if request.method == 'POST':
        message_content = request.POST.get('message_content', '')
        spam_check_result = is_spam(message_content)  # Check if the message is spam

    return render(request, 'spam/check.html', {'spam_check_result': spam_check_result, 'message_content': message_content})



@login_required
def spamlist(request):
    # Get the current user's email
    user_email = request.user.email

    # Fetch messages marked as spam where the to_address or from_address matches the current user's email
    spam_messages = Message.objects.filter(
        is_spam=True
    ).filter(
        Q(to_address=user_email) | Q(from_address=user_email)
    ).order_by('-date_sent')

    # Count unread spam messages for the current user
    unread_spam_count = Message.objects.filter(
        is_spam=True,
        to_address=user_email,
        is_read=False
    ).count()

    # Prepare profile picture URLs
    profiles = Profile.objects.all()
    profile_pics = {profile.user.email: profile.image.url for profile in profiles}
    
    # Prepare a named tuple to hold message and profile pic information
    MessageWithProfile = namedtuple('MessageWithProfile', ['message', 'profile_pic'])

    # Prepare a list to store the message and profile pic tuples
    spam_messages_with_profile_pics = []
    for message in spam_messages:
        # Determine the profile picture URL based on whether the current user is the sender or the recipient
        if message.to_address == user_email:
            # If the current user is the recipient, get the sender's profile picture
            profile_pic_url = profile_pics.get(message.from_address, '/media/default.jpg')
        else:
            # If the current user is the sender, get the recipient's profile picture
            profile_pic_url = profile_pics.get(message.to_address, '/media/default.jpg')
        
        # Append the tuple to the list
        spam_messages_with_profile_pics.append(MessageWithProfile(message=message, profile_pic=profile_pic_url))

    # Render the template with the context containing spam messages, profile pics, and unread spam message count
    return render(request, 'spam/spamlist.html', {
        'spam_messages_with_profile_pics': spam_messages_with_profile_pics,
        'count': unread_spam_count,
    })

@login_required
def search(request):
    # Get the current user's email
    user_email = request.user.email
    
    # Get the search query from the request
    query = request.GET.get('q', '')  # 'q' is the name of the input field in your form

    # Fetch messages where the current user is either the sender or the recipient, and filter by search query
    search_results = Message.objects.filter(
        Q(to_address=user_email) | Q(from_address=user_email)
    ).filter(
        Q(to_address__icontains=query) | 
        Q(from_address__icontains=query) | 
        Q(subject__icontains=query) | 
        Q(date_sent__icontains=query)
    ).order_by('-date_sent')

    # Count unread messages for the current user related to the search results
    unread_count = search_results.filter(
        to_address=user_email,
        is_read=False
    ).count()

    # Prepare profile picture URLs
    profiles = Profile.objects.all()
    profile_pics = {profile.user.email: profile.image.url for profile in profiles}

    # Prepare a named tuple to hold message and profile pic information
    MessageWithProfile = namedtuple('MessageWithProfile', ['message', 'profile_pic'])

    # Prepare a list to store the message and profile pic tuples
    search_results_with_profile_pics = []
    for message in search_results:
        # Determine the profile picture URL based on the sender or recipient
        if message.to_address == user_email:
            profile_pic_url = profile_pics.get(message.from_address, '/media/default.jpg')
        else:
            profile_pic_url = profile_pics.get(message.to_address, '/media/default.jpg')

        # Append the tuple to the list
        search_results_with_profile_pics.append(MessageWithProfile(message=message, profile_pic=profile_pic_url))

    # Render the template with the context containing search results, profile pics, and unread message count
    return render(request, 'spam/search.html', {
        'search_results_with_profile_pics': search_results_with_profile_pics,
        'count': unread_count,
        'query': query,  
    })






