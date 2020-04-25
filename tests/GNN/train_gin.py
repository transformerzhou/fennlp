#! encoding:utf-8
import time
import tensorflow as tf
from fennlp.datas import graphloader
from fennlp.metrics import Losess, Metric
from fennlp.models import GIN
from fennlp.callbacks import EarlyStopping
from fennlp.optimizers import optim

hidden_dim = 64
num_class = 6
drop_rate = 0.5
epoch = 200
early_stopping = 100
penalty = 0.01

loader = graphloader.GCNLoader(dataset="citeseer", loop=True, features_norm=True)

features, adj, y_train, y_val, y_test, train_mask, val_mask, test_mask = loader.load()

model = GIN.GINLayer(hidden_dim, num_class, drop_rate)

# optimizer = tf.keras.optimizers.Adam(0.01)
optimizer = optim.AdamWarmup(0.01, 500, weight_decay_rate=0)
crossentropy = Losess.MaskCategoricalCrossentropy()
accscore = Metric.MaskAccuracy()
stop_monitor = EarlyStopping(monitor="loss", patience=early_stopping)

# ---------------------------------------------------------
# For train
for p in range(epoch):
    t = time.time()
    with tf.GradientTape() as tape:
        predict = model(features, adj, training=True)
        loss = crossentropy(y_train, predict, train_mask)
        loss += penalty * tf.nn.l2_loss(model.variables[0])

    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(grads_and_vars=zip(grads, model.trainable_variables))

    predict_v = model.predict(features, adj)
    loss_v = crossentropy(y_val, predict_v, val_mask)
    acc = accscore(y_val, predict_v, val_mask)
    print("Epoch {} | Loss {:.4f} | Acc {:.4f} | Time {:.4f}".format(p, loss_v.numpy(), acc, time.time() - t))
    if stop_monitor(loss_v, model):
        break
# --------------------------------------------------------------------------------------
# For test
predict_t = model.predict(features, adj)
acc = accscore(y_test, predict_t, test_mask)
loss = crossentropy(y_test, predict_t, test_mask)
print("Test Loss {:.4f} | ACC {:.4f}".format(loss.numpy(), acc))
