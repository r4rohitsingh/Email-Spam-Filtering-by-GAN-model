# -*- coding: utf-8 -*-
"""fake_spam_sms_generation_GAN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1w1o-HxOFjecDw_lctnSytMQePa6CxhTX
"""

from __future__ import print_function, division

import re

import numpy as np
import pandas as pd

import spacy
import texthero as hero
from texthero import preprocessing
from sklearn.model_selection import train_test_split

from simpletransformers.language_representation import RepresentationModel

import matplotlib.pyplot as plt1

import sys

import tensorflow as tf
from tensorflow import keras

from keras.datasets import mnist
from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D
from keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Sequential

from sklearn.decomposition import PCA

from sklearn.preprocessing import MinMaxScaler

"""# # Loading dataset"""

df = pd.read_csv("SpamSMS.txt", sep="\t", header=None)
print(df.shape)
# renaming the columns
df.rename(columns={0: 'label', 1: 'text'}, inplace=True)
df.head()

# converting string labels to int labels

label_map = {
    'ham': 0,
    'spam': 1,
}

df['label'] = df['label'].map(label_map)
df.head()

df['label'].value_counts()

"""## Clean Textual data"""

def isNan(val):
     return val != val

custom_pipeline = [preprocessing.drop_no_content,
                   preprocessing.remove_urls,
                   preprocessing.remove_diacritics,
                   preprocessing.lowercase,
                   preprocessing.remove_punctuation,
                   preprocessing.remove_whitespace]

df['text'] = hero.clean(df['text'], custom_pipeline)
df.head()

model = RepresentationModel(
        model_type='bert',
        model_name='bert-base-uncased',
        use_cuda = False
    )

for i in range(1,769):
    df['f_'+str(i)]  = np.nan

df.head()

"""## Generate Embeddings"""

for index,row in df.iterrows():
    text_embed = model.encode_sentences([row["text"]], combine_strategy="mean")
    for i in range(text_embed.shape[1]):
        df.at[index, 'f_'+str(i+1)] = text_embed[0][i]

df.drop(['text'],axis=1,inplace=True)

df.head()

df.shape







"""### Fit PCA (5 components)"""

import plotly.express as px
from sklearn.decomposition import PCA

# df = px.data.iris()
# features = ["sepal_width", "sepal_length", "petal_width", "petal_length"]

pca = PCA(n_components=5)
components = pca.fit_transform(df)
labels = {
    str(i): f"PC {i+1} ({var:.1f}%)"
    for i, var in enumerate(pca.explained_variance_ratio_ * 100)
}

fig = px.scatter_matrix(
    components,
    labels=labels,
    color=df["label"]
)
fig.update_traces(diagonal_visible=False)
fig.show()

"""## Split train-test"""

train, test = train_test_split(df, test_size=0.3, random_state=42)

train.head()

train.shape

train['label'].value_counts()

test.head()

test.shape

test['label'].value_counts()

"""## Save train and test dataset (with sentence encoding) separately"""

train.to_csv('spam_training_data.csv', index=False)

test.to_csv('spam_testing_data.csv', index=False)



"""## Load train data and scaling"""

train_data = pd.read_csv('spam_training_data.csv')

train_data.head()

train_data.drop(['label'],axis=1,inplace=True)

import pandas as pd
from sklearn.preprocessing import StandardScaler

#define scaler
scaler = StandardScaler()

#create copy of DataFrame
scaled_df=train_data.copy()

#created scaled version of DataFrame
scaled_df=pd.DataFrame(scaler.fit_transform(scaled_df), columns=scaled_df.columns)

from sklearn.decomposition import PCA

#define PCA model to use
pca = PCA(n_components=10)

#fit PCA model to data
pca_fit = pca.fit(scaled_df)

import matplotlib.pyplot as plt
import numpy as np

PC_values = np.arange(pca.n_components_) + 1
plt.plot(PC_values, pca.explained_variance_ratio_, 'o-', linewidth=2, color='blue')
plt.title('Scree Plot')
plt.xlabel('Principal Component')
plt.ylabel('Variance Explained')
plt.show()



scaler = MinMaxScaler()

valid_ham_sms_data = train_data[train_data['label']==0]
valid_ham_sms_data.drop(['label'],axis=1,inplace=True)
valid_ham_sms_data.reset_index(drop=True, inplace=True)
scaler.fit_transform(valid_ham_sms_data)
valid_ham_sms_data.head()

valid_ham_sms_data['label']=0
valid_ham_sms_data.head()

valid_spam_sms_data = train_data[train_data['label']==1]
valid_spam_sms_data.drop(['label'],axis=1,inplace=True)
valid_spam_sms_data.reset_index(drop=True, inplace=True)
scaler.fit_transform(valid_spam_sms_data)
valid_spam_sms_data.head()

"""## Generating fake spam SMS using GAN"""

class GAN():
    def __init__(self):
        self.latent_dim = 100

        optimizer = Adam(0.0002, 0.5)

        # Build and compile the discriminator
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='mse',
            optimizer=optimizer,
            metrics=['accuracy'])

        # Build the generator
        self.generator = self.build_generator()

        # The generator takes noise as input and generates imgs
        z = Input(shape=(self.latent_dim,))
        img = self.generator(z)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        validity = self.discriminator(img)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(z, validity)
        self.combined.compile(loss='mse', optimizer=optimizer)


    def build_generator(self):

        model = Sequential()

        model.add(Dense(256, input_dim=self.latent_dim))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(768))
        model.add(LeakyReLU(alpha=0.2))

        model.summary()

        noise = Input(shape=(self.latent_dim,))
        img = model(noise)

        return Model(noise, img)

    def build_discriminator(self):

        model = Sequential()

        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dense(256))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dense(1, activation='sigmoid'))


        img = Input(shape=(768,))
        validity = model(img)

        model.summary()
        return Model(img, validity)

    def train(self, epochs, batch_size=128):

        # Load the scaled dataset
        X_train = valid_spam_sms_data

        # Adversarial ground truths
        valid = np.ones((batch_size, 1))
        fake = np.zeros((batch_size, 1))

        for epoch in range(epochs):

            # ---------------------
            #  Train Discriminator
            # ---------------------

            # Select a random batch of images
            idx = np.random.randint(0, X_train.shape[0], batch_size)
            imgs = X_train.loc[idx]

            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))

            # Generate a batch of new images
            gen_imgs = self.generator.predict(noise)

            # Train the discriminator
            d_loss_real = self.discriminator.train_on_batch(imgs, valid)
            d_loss_fake = self.discriminator.train_on_batch(gen_imgs, fake)
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            # ---------------------
            #  Train Generator
            # ---------------------

            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))

            # Train the generator (to have the discriminator label samples as valid)
            g_loss = self.combined.train_on_batch(noise, valid)

            # Plot the progress
            print ("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, d_loss[0], 100*d_loss[1], g_loss))


    def sample_images(self, num):
        # r, c = 5, 5
        noise = np.random.normal(0.5, 0.5, (num, self.latent_dim))

        gen_imgs = self.generator.predict(noise)

        # Rescale images 0 - 1
        gen_imgs = 0.5 * gen_imgs + 0.5
        print(gen_imgs)
        print("_____------____")
        return gen_imgs



if __name__ == '__main__':
    gan = GAN()
    gan.train(epochs=1000, batch_size=32)

invalid_spam_sms_data = gan.sample_images(3000)

invalid_spam_sms_data.shape

new_train_set = pd.DataFrame(invalid_spam_sms_data, columns=['f_1','f_2','f_3','f_4','f_5','f_6','f_7','f_8','f_9','f_10','f_11','f_12','f_13','f_14','f_15','f_16','f_17','f_18','f_19','f_20','f_21','f_22','f_23','f_24','f_25','f_26','f_27','f_28','f_29','f_30','f_31','f_32','f_33','f_34','f_35','f_36','f_37','f_38','f_39','f_40','f_41','f_42','f_43','f_44','f_45','f_46','f_47','f_48','f_49','f_50','f_51','f_52','f_53','f_54','f_55','f_56','f_57','f_58','f_59','f_60','f_61','f_62','f_63','f_64','f_65','f_66','f_67','f_68','f_69','f_70','f_71','f_72','f_73','f_74','f_75','f_76','f_77','f_78','f_79','f_80','f_81','f_82','f_83','f_84','f_85','f_86','f_87','f_88','f_89','f_90','f_91','f_92','f_93','f_94','f_95','f_96','f_97','f_98','f_99','f_100','f_101','f_102','f_103','f_104','f_105','f_106','f_107','f_108','f_109','f_110','f_111','f_112','f_113','f_114','f_115','f_116','f_117','f_118','f_119','f_120','f_121','f_122','f_123','f_124','f_125','f_126','f_127','f_128','f_129','f_130','f_131','f_132','f_133','f_134','f_135','f_136','f_137','f_138','f_139','f_140','f_141','f_142','f_143','f_144','f_145','f_146','f_147','f_148','f_149','f_150','f_151','f_152','f_153','f_154','f_155','f_156','f_157','f_158','f_159','f_160','f_161','f_162','f_163','f_164','f_165','f_166','f_167','f_168','f_169','f_170','f_171','f_172','f_173','f_174','f_175','f_176','f_177','f_178','f_179','f_180','f_181','f_182','f_183','f_184','f_185','f_186','f_187','f_188','f_189','f_190','f_191','f_192','f_193','f_194','f_195','f_196','f_197','f_198','f_199','f_200','f_201','f_202','f_203','f_204','f_205','f_206','f_207','f_208','f_209','f_210','f_211','f_212','f_213','f_214','f_215','f_216','f_217','f_218','f_219','f_220','f_221','f_222','f_223','f_224','f_225','f_226','f_227','f_228','f_229','f_230','f_231','f_232','f_233','f_234','f_235','f_236','f_237','f_238','f_239','f_240','f_241','f_242','f_243','f_244','f_245','f_246','f_247','f_248','f_249','f_250','f_251','f_252','f_253','f_254','f_255','f_256','f_257','f_258','f_259','f_260','f_261','f_262','f_263','f_264','f_265','f_266','f_267','f_268','f_269','f_270','f_271','f_272','f_273','f_274','f_275','f_276','f_277','f_278','f_279','f_280','f_281','f_282','f_283','f_284','f_285','f_286','f_287','f_288','f_289','f_290','f_291','f_292','f_293','f_294','f_295','f_296','f_297','f_298','f_299','f_300','f_301','f_302','f_303','f_304','f_305','f_306','f_307','f_308','f_309','f_310','f_311','f_312','f_313','f_314','f_315','f_316','f_317','f_318','f_319','f_320','f_321','f_322','f_323','f_324','f_325','f_326','f_327','f_328','f_329','f_330','f_331','f_332','f_333','f_334','f_335','f_336','f_337','f_338','f_339','f_340','f_341','f_342','f_343','f_344','f_345','f_346','f_347','f_348','f_349','f_350','f_351','f_352','f_353','f_354','f_355','f_356','f_357','f_358','f_359','f_360','f_361','f_362','f_363','f_364','f_365','f_366','f_367','f_368','f_369','f_370','f_371','f_372','f_373','f_374','f_375','f_376','f_377','f_378','f_379','f_380','f_381','f_382','f_383','f_384','f_385','f_386','f_387','f_388','f_389','f_390','f_391','f_392','f_393','f_394','f_395','f_396','f_397','f_398','f_399','f_400','f_401','f_402','f_403','f_404','f_405','f_406','f_407','f_408','f_409','f_410','f_411','f_412','f_413','f_414','f_415','f_416','f_417','f_418','f_419','f_420','f_421','f_422','f_423','f_424','f_425','f_426','f_427','f_428','f_429','f_430','f_431','f_432','f_433','f_434','f_435','f_436','f_437','f_438','f_439','f_440','f_441','f_442','f_443','f_444','f_445','f_446','f_447','f_448','f_449','f_450','f_451','f_452','f_453','f_454','f_455','f_456','f_457','f_458','f_459','f_460','f_461','f_462','f_463','f_464','f_465','f_466','f_467','f_468','f_469','f_470','f_471','f_472','f_473','f_474','f_475','f_476','f_477','f_478','f_479','f_480','f_481','f_482','f_483','f_484','f_485','f_486','f_487','f_488','f_489','f_490','f_491','f_492','f_493','f_494','f_495','f_496','f_497','f_498','f_499','f_500','f_501','f_502','f_503','f_504','f_505','f_506','f_507','f_508','f_509','f_510','f_511','f_512','f_513','f_514','f_515','f_516','f_517','f_518','f_519','f_520','f_521','f_522','f_523','f_524','f_525','f_526','f_527','f_528','f_529','f_530','f_531','f_532','f_533','f_534','f_535','f_536','f_537','f_538','f_539','f_540','f_541','f_542','f_543','f_544','f_545','f_546','f_547','f_548','f_549','f_550','f_551','f_552','f_553','f_554','f_555','f_556','f_557','f_558','f_559','f_560','f_561','f_562','f_563','f_564','f_565','f_566','f_567','f_568','f_569','f_570','f_571','f_572','f_573','f_574','f_575','f_576','f_577','f_578','f_579','f_580','f_581','f_582','f_583','f_584','f_585','f_586','f_587','f_588','f_589','f_590','f_591','f_592','f_593','f_594','f_595','f_596','f_597','f_598','f_599','f_600','f_601','f_602','f_603','f_604','f_605','f_606','f_607','f_608','f_609','f_610','f_611','f_612','f_613','f_614','f_615','f_616','f_617','f_618','f_619','f_620','f_621','f_622','f_623','f_624','f_625','f_626','f_627','f_628','f_629','f_630','f_631','f_632','f_633','f_634','f_635','f_636','f_637','f_638','f_639','f_640','f_641','f_642','f_643','f_644','f_645','f_646','f_647','f_648','f_649','f_650','f_651','f_652','f_653','f_654','f_655','f_656','f_657','f_658','f_659','f_660','f_661','f_662','f_663','f_664','f_665','f_666','f_667','f_668','f_669','f_670','f_671','f_672','f_673','f_674','f_675','f_676','f_677','f_678','f_679','f_680','f_681','f_682','f_683','f_684','f_685','f_686','f_687','f_688','f_689','f_690','f_691','f_692','f_693','f_694','f_695','f_696','f_697','f_698','f_699','f_700','f_701','f_702','f_703','f_704','f_705','f_706','f_707','f_708','f_709','f_710','f_711','f_712','f_713','f_714','f_715','f_716','f_717','f_718','f_719','f_720','f_721','f_722','f_723','f_724','f_725','f_726','f_727','f_728','f_729','f_730','f_731','f_732','f_733','f_734','f_735','f_736','f_737','f_738','f_739','f_740','f_741','f_742','f_743','f_744','f_745','f_746','f_747','f_748','f_749','f_750','f_751','f_752','f_753','f_754','f_755','f_756','f_757','f_758','f_759','f_760','f_761','f_762','f_763','f_764','f_765','f_766','f_767','f_768'])
new_train_set['label']=1

data = pd.concat([new_train_set, valid_ham_sms_data],axis=0)

data = data.sample(frac=1)
data.head()

data['label'].value_counts()

"""## PCA for GAN generated fake spam SMS"""

import plotly.express as px
from sklearn.decomposition import PCA

# df = px.data.iris()
# features = ["sepal_width", "sepal_length", "petal_width", "petal_length"]

pca = PCA(n_components=5)
components = pca.fit_transform(data)
labels = {
    str(i): f"PC {i+1} ({var:.1f}%)"
    for i, var in enumerate(pca.explained_variance_ratio_ * 100)
}

fig = px.scatter_matrix(
    components,
    labels=labels,
    color=data["label"]
)
fig.update_traces(diagonal_visible=False)
fig.show()

"""## Determine Quality of fake data using classifiers"""

X_train = data.drop(['label'], axis=1)
y_train = data['label']

X_test = pd.read_csv('spam_testing_data.csv')
y_test = X_test['label']
X_test.drop(['label'],axis=1,inplace=True)
#X_test = scaler.fit_transform(X_test)
X_test.head()

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

classifier = LogisticRegression()
classifier.fit(X_train, y_train)
classifier.score(X_test, y_test)

y_predicted = classifier.predict(X_test)

cm = confusion_matrix(y_test, y_predicted)
cm

from sklearn import tree

tree_classifier = tree.DecisionTreeClassifier()
tree_classifier.fit(X_train,y_train)
tree_classifier.score(X_test, y_test)

y_predicted = tree_classifier.predict(X_test)

cm = confusion_matrix(y_test, y_predicted)
cm

from sklearn.svm import SVC

sv_classifier = SVC(C=10, kernel='poly')
sv_classifier.fit(X_train,y_train)
sv_classifier.score(X_test, y_test)

y_predicted = tree_classifier.predict(X_test)

cm = confusion_matrix(y_test, y_predicted)
cm

from sklearn.linear_model import SGDClassifier

clf = SGDClassifier()
clf.fit(X_train,y_train)
clf.score(X_test,y_test)

y_predicted = tree_classifier.predict(X_test)

cm = confusion_matrix(y_test, y_predicted)
cm

from sklearn.ensemble import RandomForestClassifier

rfc = RandomForestClassifier(n_estimators=40)
rfc.fit(X_train,y_train)
rfc.score(X_test,y_test)

y_predicted = rfc.predict(X_test)

cm = confusion_matrix(y_test, y_predicted)
cm

