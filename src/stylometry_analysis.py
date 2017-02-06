from __future__ import division
from string import punctuation
import numpy as np
from textblob import TextBlob

class StyleFeatures(dict):

    def find_freq(self,lst, search_item, normalizer):
        return lst.count(search_item) / len(normalizer)

    def __init__(self,article):

        article= TextBlob(article)
        words = [word.singularize() for word in article.words]
        sentences = article.sentences

        self['polarity'] = article.sentiment.polarity
        self['subjectivity'] = article.sentiment.subjectivity

        word_lens = [len(word) for word in words]
        sentence_lens = [len(sentence.split()) for sentence in sentences]
        punct = [char for char in article if char in punctuation]

        self['article_len'] = len(words)
        if self['article_len'] != 0:
            self['type_token_ratio'] = len(set(words)) / self['article_len']
            self['mean_word_len'] = np.mean(word_lens)
            self['mean_sentence_len'] = np.mean(sentence_lens)
            self['std_sentence_len'] = np.std(sentence_lens)

            self['freq_commas'] = self.find_freq(punct, ',', words) * 1000
            self['freq_semi_colons'] = self.find_freq(punct, ';', words) * 1000
            self['freq_question_marks'] = self.find_freq(punct, '?', sentences)
            self['freq_exclamation_marks'] = self.find_freq(punct, '!', sentences)
            self['freq_quotation_marks'] = self.find_freq(punct, '"', sentences)
            self['freq_ands'] = self.find_freq(words, 'and', words) * 1000
            self['freq_buts'] = self.find_freq(words, 'but', words) * 1000
            self['freq_howevers'] = self.find_freq(words, 'however', words) * 1000
            self['freq_ifs'] = self.find_freq(words, 'if', words) * 1000
            self['freq_thats'] = self.find_freq(words, 'that', words) * 1000
            self['freq_mores'] = self.find_freq(words, 'more', words) * 1000
            self['freq_verys'] = self.find_freq(words, 'very', words) * 1000
