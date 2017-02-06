from __future__ import division
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from stop_words import get_stop_words
from itertools import izip
from string import punctuation
from stylometry_analysis import StyleFeatures
import json
from datetime import datetime
import time
from collections import defaultdict, Counter
from itertools import izip
from Classifiers import Classifiers
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from scipy.stats import mode
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from BaselineClassifiers import BaselineClassifier, MajorityClassifier, SmartBaseline
from plotting import plot_feature_vs_date, plot_top_countries_for_each_newssite,\
            plot_gender_by_newssite, get_gender_percentages, plot_features_by_gender,plot_gender_vs_time
from BaselineClassifiers import BaselineClassifier, MajorityClassifier
from Filtering import filter_data, filter_out_unknowns, group_by_month,group_by_author,seperate_by_gender
from vectorizer_and_kmeans_clf import vectorize_articles, add_meta_data_to_tfidf_mat 
import cPickle
from plotting import plot_clf_scores,print_top_words_of_all_articles
from sklearn.metrics import recall_score, precision_score, f1_score, accuracy_score,confusion_matrix, roc_curve, auc
from scipy.stats import hmean
import matplotlib.cm as cm 

# HOW DO I SORT ABOVE???


with open('text_files/female_names.txt') as f:
    FEMALE_NAMES = set(f.read().splitlines())
with open('text_files/male_names.txt') as f:
    MALE_NAMES = set(f.read().splitlines())

def get_author_gender(name):
    '''
    Input: name of author
    Output: string "female", "male", or "unknown"
    '''

    if name in FEMALE_NAMES:
        return 'female'
    elif name in MALE_NAMES:
        return 'male'
    return 'unknown'



def open_and_filter_data(newssite, filter_date= False,min_year= None):
    df = pd.read_json('feature_data/{}_features.json'.format(newssite))

    print '____________________{}____________________'.format(newssite)
    print '{} datapoints retreived'.format(len(df))

    df = filter_data(df,filter_date,min_year)
    return df

def get_df_and_grouped_df(newssite,filter_date= False,min_date= None):
    df = open_and_filter_data(newssite,filter_date,min_date)
    grouped_by_author_df = group_by_author(df)
    return df, grouped_by_author_df

def find_top_words_of_articles():
    pass

def combine_data(data):
    return pd.concat(data)

def get_y_target_values(data,target_feature):
    y = data.copy()
    y = y[target_feature].reset_index()
    y= y.replace(to_replace=['female','male'],value=[0,1])
    y= y[target_feature].astype(int)
    return np.array(y)

def run_all_classifiers(data):
    X = data[data.author_gender != 'unknown']

    #text = X['article'] 

    y = get_y_target_values(X,'author_gender')
    X.drop(['author_gender','article','title','date_posted','year','newssite','average_date'],axis=1, inplace=True)
    #X = X[['article_len','mean_sentence_len','mean_word_len','type_token_ratio', \
    #        'freq_ifs','freq_quotation_marks','freq_semi_colons','freq_verys','polarity',\
    #        'std_sentence_len','subjectivity']]


    min_polarity = X['polarity'].min()
    X['polarity'] = X['polarity'] + (min_polarity * -1)

    X = X.reset_index()
    X.drop('author',axis=1,inplace=True) 


    #X = vectorize_articles(text,meta_data=X)

    #X = X.toarray()


    print X.columns
    '''
    X = pd.get_dummies(X)
    X.drop('newssite_time',axis=1,inplace=True)
    X['constant'] = 1
    '''

    #tfidf_mat = vectorize_articles(X['article'])

    '''
    clfs = [MultinomialNB(),BaselineClassifier(percentage = len(y[y==1])/len(y), length = int(len(y) * 0.25)+1), \
            MajorityClassifier(majority = 1,length = int(len(y) * 0.25)+1)]
    '''
    '''
    clfs = [AdaBoostClassifier(n_estimators=100,learning_rate= 0.05), \
                    GradientBoostingClassifier(n_estimators=80,learning_rate= 0.05,max_depth=1),\
                    RandomForestClassifier(n_estimators=100, max_depth=20, criterion='gini'), DecisionTreeClassifier(),\
                    LogisticRegression(), MultinomialNB(),\
                    BaselineClassifier(percentage = len(y[y==1])/len(y) ,length = int(len(y) * 0.25)+1), \
                    MajorityClassifier(majority = 1, length = int(len(y) * 0.25)+1)]
    '''
    
    clfs = [AdaBoostClassifier(n_estimators=100,learning_rate= 0.05), \
                    RandomForestClassifier(n_estimators=100, max_depth=20, criterion='gini')]

    gender_model = Classifiers(clfs)
    #gender_model = Classifiers([RandomForestClassifier()])
    gender_model.train(X,y) # train on train data
    #gender_model.cross_validate(X,y)
    #gender_model.plot_roc_curve() # run on test data

    #gender_model.test()

def open_cPickle_file(filename):
    with open(filename, 'rb') as f:
        return cPickle.load(f)

def f1_harmonic_mean(y_true, y_pred):
        cm = confusion_matrix(y_true, y_pred)

        TN = cm[0][0]
        FP = cm[0][1]
        FN = cm[1][0]
        TP = cm[1][1]

        if TN == 0:
            TN = 1
        if TP == 0:
            TP = 1

        inv_precision = TN/(TN+FN) #Proportion of those identified as negative that actually are.
        inv_recall = TN/(FP+TN) #Proportion of those *actually*  negative identified as such.

        inverted_f1 = hmean([inv_recall, inv_precision])
        harmonic_f1 = hmean([f1_score(y_true, y_pred), inverted_f1])
        mean_f1 = np.mean([f1_score(y_true, y_pred), inverted_f1])

        return harmonic_f1, mean_f1

def test_model(classifiers,classifier_names,X,y_true,plot_name):
        f1_means = []
        f1_har = []
        for name, clf in zip(classifier_names, classifiers):
            print '{} results:'.format(name)
            predictions = clf.predict(X)

            harmonic,regular = f1_harmonic_mean(y_true, predictions)

            f1_means.append(regular)
            f1_har.append(harmonic)

            print "Mean f1: {:.3%}".format(regular)
            print "Harmonic f1: {:.3%}".format(harmonic)
            print "\n" 
        plot_clf_scores(f1_means,classifier_names,plot_name)
        plot_clf_scores(f1_har,classifier_names,'harmonic' + plot_name)

def run_test(data, plot_name):
    X = data[data.author_gender != 'unknown']

    fitted_tfidf = open_cPickle_file('TFIDF_fit')
    text = fitted_tfidf.transform(X['article'])

    y = get_y_target_values(X,'author_gender')
    '''
    X.drop(['author','author_gender','article','title','date_posted',\
            'year','newssite',\
            'countries_in_title','ME_countries','countries','style_features'],axis=1, inplace=True)
    '''
    
    X.drop(['author','author_gender','article','title','date_posted',\
            'year','newssite','countries_in_title'],axis=1,inplace=True) 

    min_polarity = X['polarity'].min()
    X['polarity'] = X['polarity'] + (min_polarity * -1)

    #X_tfidf = add_meta_data_to_tfidf_mat(text,X)

    #X_tfidf = X_tfidf.toarray()

    #fitted_ada = open_cPickle_file('Fitted_Model_AdaBoostClassifier')
    #fitted_rf = open_cPickle_file('Fitted_Model_RandomForestClassifier')
    fitted_ada_style = open_cPickle_file('Fitted_Model_AdaBoostClassifier_Style')
    fitted_rf_style = open_cPickle_file('Fitted_Model_RandomForestClassifier_Style')

    #clfs = [BaselineClassifier(percentage = len(y[y==1])/len(y) ,length=len(y)), \
    #               MajorityClassifier(majority = 1, length=len(y)), fitted_ada, fitted_rf]

    style_clfs = [MajorityClassifier(majority = 1, length=len(y)),\
                    BaselineClassifier(percentage = len(y[y==1])/len(y) ,length=len(y)), \
                        fitted_ada_style]

    classifier_names = ['Majority Baseline', 'Random Baseline', 'Ada Boost']
    #test_model(clfs,classifier_names,X_tfidf,y, 'scores_clf.jpg')
    test_model(style_clfs,classifier_names,X,y, plot_name)

if __name__ == "__main__":
    media_sites = ['BuzzFeed','TIME', 'TIME_Opinion','Atlantic']

    #media_sites = ['Time_opinion']

    #media_sites = ['Slate','Breitbart']

    media_data = []
    media_grouped_data = []
    for media_name in media_sites:
        data,grouped_data = get_df_and_grouped_df(media_name,filter_date=True,min_date=2011)
        media_data.append(data)
        media_grouped_data.append(grouped_data)

    
    combined_data = combine_data(media_grouped_data)
    
    '''
    print 'Start' 
    run_test(combined_data, 'combined.jpg')
    run_test(media_data[0], 'slate.jpg')
    run_test(media_data[0], 'bb.jpg')

    print 'Finished'
    '''

    '''
    female_words, female_tfidf = vectorize_articles(female_data['article'])
    top_inds = np.argsort(female_tfidf.idf_)[-10:]
    top_female_words = get_words(top_inds,female_tfidf)
    male_words, male_tfidf = vectorize_articles(male_data['article'])
    top_inds = np.argsort(male_tfidf.idf_)[-10:]
    top_male_words = get_words(top_inds,male_tfidf)

    print 'Female words:'
    print top_female_words
    print 'Male words:'
    print top_male_words
    '''

    female_data, male_data = seperate_by_gender(combined_data)
    female_topics = print_top_words_of_all_articles(female_data['article'])
    male_topics = print_top_words_of_all_articles(male_data['article'])
    
    #get_top_words_from_kmeans([female_data,male_data],['female','male'])

    

    '''
    combined_data = combine_data(media_data)
    combined_data.reset_index
    combined_data.drop('index',axis=1,inplace=True)
    '''

    
 
    #combined_grouped_data = combine_data(media_grouped_data)
    #plot_gender_vs_time(combined_grouped_data) # similar ratio of men to women per year
    # slate has more males than females compared to the other newssite. remove to make sure effect is due to gender and not newssite
    
    #combined_data_no_slate = combine_data(media_grouped_data[1:])

    #plot_features_by_gender(combined_grouped_data,'images-gender/{}_by_gender.jpg')
    #plot_features_by_gender(combined_data_no_slate,'images-gender-no-slate/{}_by_gender.jpg')
    #plot_features_by_gender(media_grouped_data[3],'images-gender-opinion/{}_by_gender.jpg')
   
    '''
    newsite_colors = ['dodgerblue','orangered','olive','gold','gray','lightcoral']
    gender_colors = ['dimgray','indianred']

    plot_feature_vs_date(media_grouped_data, media_sites,'images/{}.jpg',colors=newsite_colors)
    #plot_gender_by_newssite(media_grouped_data,media_sites)
    plot_top_countries_for_each_newssite(media_data, media_sites)
    '''

    #create_node_graph(combined_data,'countries_in_titles_connections.gml')

    #run_all_classifiers(combined_data_no_slate)

    '''
    gender_model = NaiveBayesPredictor()
    gender_model.train(X,y)
    #gender_model.cross_validate(y)
    #gender_model.test_results(y, average= 'macro')
    #gender_model.test_results()

    print 'Naive Bayes news model'
    X = combined_data['article'].reset_index()
    y = np.array(combined_data['newssite'])
    gender_model = NaiveBayesPredictor()
    gender_model.train(X,y)
    gender_model.cross_validate(y, average= 'macro')
    #gender_model.test_results(y, average='macro')
    #gender_model.test_results()
    '''
