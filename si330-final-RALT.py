from urllib.request import urlopen
from bs4 import BeautifulSoup
import re, json, string, urllib, math, csv


# Spaces like these are placed throughout the code to make the results easier to view
print ('')
print ('')

# Get the user's artist of choice as a global variable so that it can be used throughout the code
global user_choice
user_choice = str(input("Enter an artist's name: ")).lower()

print ('')


# If the artist's name consists of more than one word, this function will insert a '+' between the names,
# as this is how it needs to be formatted for the iTunes API request, and return that formatted string
def get_artist():
    separate = user_choice.split()
    insert_plus = '+'.join(separate)
    return insert_plus


# Set artist variable equal to the correctly formatted user's input
artist = get_artist()



# This function sorts through the JSON dictionary returned from the iTunes API request with the given artist and created URL,
# and grabs the amount of song titles set by the 'limit' term in the URL, returning a list of these song titles
# It also eliminates the (feat. _____) section from a song's title, as this does not appear in the AZLyrics URL
def get_songs(baseurl = 'https://itunes.apple.com/search?term=' + artist + '&limit=10'): # Limit is currently set to a smaller number to try to avoid being blocked by AZLyrics
    response = urlopen(baseurl)
    html = response.read().decode('utf-8')
    songs = json.loads(html)
    song_list = []
    for num in range(10): # MAKE SURE THIS NUMBER IS THE SAME AS THE LIMIT
        song_list.append((songs['results'][num]['trackName']))
    song_list2 = []
    for track in song_list:
        separate2 = track.split()
        if '(feat.' not in separate2:
            no_space = ''.join(separate2)
            song_list2.append(no_space.lower())
        else:
            match = re.search(r'(.*)(\s\(feat\..*)', track)
            no_space = (match.group(1)).replace(' ', '')
            song_list2.append(no_space.lower())
    return song_list2



# This function creates the URL that will feature the web page of lyrics for each song
# collected from the given artist in the previous function
# If the artist's name begins with 'The', such as 'The Beatles', the 'The' will be removed since AZLyrics
# does not include it in its URLs
# Punctuation is removed also removed from the song names when need be, as punctuation does not appear in the URLs
# A list of properly formatted links is returned
def create_azlyrics_url():
    base = 'http://www.azlyrics.com/lyrics/'
    if 'the' in user_choice:
        user_choice2 = user_choice.replace('the', '')
        add_artist = base + ''.join(user_choice2.split())
    else:
        add_artist = base + ''.join(user_choice.split())
    songs = get_songs()
    link_list = []
    for track in songs:
        for char in string.punctuation:
            track = track.replace(char, "")
            link = add_artist + '/' + track + '.html'
        link_list.append(link)
    return link_list



# This function uses BeautifulSoup to parse the HTML of the lyric pages on AZLyrics and grabs those lyrics for analysis,
# storing and returning them in a list
# A lot of formatting and removal of junk using regular expressions and the replace method is implemented to strictly
# get just the lyrics from the web page and nothing extra
# If the web page cannot be reached for whatever reason, the code controls for this
# and will simply continue to the next link in the list of links
def get_lyrics():
    links = create_azlyrics_url()
    lyric_list = []
    for url in links:
        try:
            results = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(results, 'html.parser')
            lyrics = str(soup)
            top_junk = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
            bottom_junk = '<!-- MxM banner -->'
            lyrics = lyrics.split(top_junk)[1]
            lyrics = lyrics.split(bottom_junk)[0]
            lyrics = lyrics.replace('<br>', '').replace('</br>', '').replace('</div>', '').replace('<i>', '').replace('</i>', '').strip()
            no_brackets = re.sub(r'\[.*\]', '', lyrics)
            no_new_line = re.sub(r'\n', ' ', no_brackets)
            no_punc = re.sub(r'[.?,;!"\\)(]', '', no_new_line)
            lyric_list.append(no_punc.lower())
        except Exception:
            continue
    return lyric_list



# IDF dictionary is created and made into a global variable so that it can be used in multiple places going forward
global idf
idf = dict()



# This function takes in a string of lyrics and creates a dictionary of all of the words in a single song
# with the word’s count as its corresponding value, and returns this dictionary
# A dictionary of the words across all of the songs is also created, where the value for each word is now how many times it appears across all songs
# These values will be used as the denominator in the logarithmic part of the TF-IDF formula
def term_frequency(lyrics):
    tf = dict()
    for word in lyrics.split():
        if word in tf:
            tf[word] += 1
        else:
            tf[word] = 1
            if word in idf:
                idf[word] += 1
            else:
                idf[word] = 1
    num_words = len(lyrics.split())
    for word in tf:
        tf[word] = tf[word] / num_words
    return tf



# This function takes in a list of lyrics and uses the data from the term_frequency function to return a dictionary of dictionaries
# of the total term frequencies for the lyrics of each song
def get_total_tf(song):
    total_tf = dict()
    for idx, val in enumerate(song):
        occurrences = term_frequency(val)
        total_tf[idx] = occurrences
    return total_tf



# This function takes in a dictionary of dictionaries of term frequency values, as well as the total number of songs collected,
# and creates a dictionary of dictionaries for each song to hold the lyrics' TF-IDF values
# Each word is given its TF-IDF value using the formula, comprised of data from the aforementioned functions
# A dictionary of dictionaries in which the inner dictionary is comprised of lyrics and their TF-IDF values is returned
def get_tfidf(tf, num_of_songs):
    tfidf = dict()
    for count in tf:
        tfidf[count] = dict()
        for word in tf[count]:
            tfidf[count][word] = tf[count][word] * math.log(num_of_songs / idf[word])
    return tfidf




def main():
    song = get_lyrics() # Get list of lyrics separated by song

    count = len(song) # Calculate number of songs analyzed for numerator of logarithmic portion of TF-IDF formula

    tf = get_total_tf(song) # Implement this function using the list of lyrics for the given artist
    tfidf = get_tfidf(tf, count) # Implement this function using the dictionary created in the function above and the total number of songs to calculate all of the TF-IDF values


    # Extract each word and its corresponding TF-IDF value as a pair and put them together in a tuple,
    # then append the tuples to a list, allowing for easy sorting and getting just the information wanted
    tfidf_values = []
    for dic in tfidf.values():
        for pair in dic:
            tfidf_values.append((pair, dic[pair]))


    sorted_tfidf = sorted(tfidf_values, key=lambda x: x[1], reverse=True) # Sort the list of tuples in descending order by TF-IDF value (words with higher TF-IDF values come first)



    # Print each word and its corresponding TF-IDF value in the console for the user to view
    # Note: words can appear more than once in the output, as they have different TF-IDF values for each song they appear in
    print ('')
    print ('**************************************')
    print ('          word: tf-idf value          ')
    print ('**************************************')
    print ('')
    for pair in sorted_tfidf:
        print (pair[0] + ': ' + str(pair[1]))


    # Create CSV file for the output above to use to make the visualization (with limitations stated below)
    with open('si330-final-RALT.csv', 'w', newline='') as output_file:

        tfidf_data_writer = csv.DictWriter(output_file,
                                             fieldnames=['WORD', 'TF-IDF VALUE'],
                                             extrasaction='ignore',
                                             delimiter=',', quotechar='"')

        tfidf_data_writer.writeheader()

        for pair in sorted_tfidf[0:100]: # Only get top 100 words based on their TF-IDF values for visualization purposes
            tfidf_data_writer.writerow({'WORD':pair[0], 'TF-IDF VALUE':pair[1]*1000}) # Multiply TF-IDF value by large number for visualization purposes




if __name__ == '__main__':
    main()