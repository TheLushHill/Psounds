# GPT语义模型训练代码

import datetime
import os
import pdb

if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]
import argparse
import logging
from pathlib import Path

import torch, platform
from pytorch_lightning import seed_everything
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger  # WandbLogger
from pytorch_lightning.strategies import DDPStrategy
from AR.data.data_module import Text2SemanticDataModule
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from AR.utils.io import load_yaml_config

logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
torch.set_float32_matmul_precision("high")
from AR.utils import get_newest_ckpt
from collections import OrderedDict
from time import time as ttime
import shutil
def my_save(fea,path):
    dir=os.path.dirname(path)
    name=os.path.basename(path)
    tmp_path="%s.pth"%(ttime())
    torch.save(fea,tmp_path)
    
# 重写pytorch的ModelCheckpoint类，实现保存最新的ckpt和自定义保存路径
class my_model_ckpt(ModelCheckpoint):
    def __init__(
        self,
        config,                    
        if_save_latest,            
        if_save_every_weights,     
        half_weights_save_dir,
        exp_name,
        **kwargs
    ):
        super().__init__(**kwargs) # 调用父类的构造函数，读取父类属性
        self.if_save_latest = if_save_latest
        self.if_save_every_weights = if_save_every_weights
        self.half_weights_save_dir = half_weights_save_dir
        self.exp_name = exp_name
        self.config = config

    def on_train_epoch_end(self, trainer, pl_module):
        # 如果不跳过保存检查点且在训练周期结束时保存检查点：
        if self._should_save_on_train_epoch_end(trainer):
            monitor_candidates = self._monitor_candidates(trainer)    # 获取监视器的候选项
            if (
                self._every_n_epochs >= 1
                and (trainer.current_epoch + 1) % self._every_n_epochs == 0
            ):
                if (
                    self.if_save_latest == True
                ):  #如果设置只保存最后一个ckpt，在保存下一个ckpt后要清理掉之前的所有ckpt
                    to_clean = list(os.listdir(self.dirpath))
                self._save_topk_checkpoint(trainer, monitor_candidates)
                if self.if_save_latest == True:
                    for name in to_clean:
                        try:
                            os.remove("%s/%s" % (self.dirpath, name))
                        except:
                            pass
                if self.if_save_every_weights == True:
                    to_save_od = OrderedDict()
                    to_save_od["weight"] = OrderedDict()
                    dictt = trainer.strategy._lightning_module.state_dict()
                    for key in dictt:
                        to_save_od["weight"][key] = dictt[key].half()
                    to_save_od["config"] = self.config
                    to_save_od["info"] = "GPT_e%s" % (trainer.current_epoch + 1)
                    # torch.save(
                    my_save(
                        to_save_od,
                        "%s/%s_e%s.ckpt"
                        % (
                            self.half_weights_save_dir,
                            self.exp_name,
                            trainer.current_epoch + 1,
                        ),
                    )
            self._save_last_checkpoint(trainer, monitor_candidates)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config_file",
        type=str,
        default="Model/Training/GS_Model/configs/s1longer_v2.yaml",
        help="path of config file",
    )
    return parser.parse_args()

# 外部直接调用该函数
def main(args,exp_name):
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "7000"          # 改为小于10000的端口
    
    config = load_yaml_config(args.config_file)

    output_dir = Path(f"Model/trained/{exp_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    ckpt_dir = output_dir / "ckpt"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    seed_everything(config["train"]["seed"], workers=True)
    ckpt_callback: ModelCheckpoint = my_model_ckpt(
        config=config,
        if_save_latest=config["train"]["if_save_latest"],
        if_save_every_weights=config["train"]["if_save_every_weights"],
        half_weights_save_dir=config["train"]["half_weights_save_dir"],
        exp_name=exp_name,
        save_top_k=-1,
        monitor="top_3_acc",
        mode="max",
        save_on_train_epoch_end=True,
        every_n_epochs=config["train"]["save_every_n_epoch"],
        dirpath=ckpt_dir,
    )
    os.makedirs(output_dir, exist_ok=True)
    logger = TensorBoardLogger(name=exp_name, save_dir=str(output_dir))  

    trainer: Trainer = Trainer(
        max_epochs=config["train"]["epochs"],
        accelerator="gpu" if torch.cuda.is_available() else "cpu",
        # val_check_interval=9999999999999999999999,###不要验证
        # check_val_every_n_epoch=None,
        limit_val_batches=0,
        devices=-1 if torch.cuda.is_available() else 1,
        benchmark=False,
        fast_dev_run=False,
        strategy = DDPStrategy(
            process_group_backend="gloo" # if platform.system() != "Windows" else "gloo"
        )
        if torch.cuda.is_available() else "auto",
        precision=config["train"]["precision"],
        logger=logger,
        num_sanity_val_steps=0,
        callbacks=[ckpt_callback],
    )

    model: Text2SemanticLightningModule = Text2SemanticLightningModule(
        config, output_dir
    )

    data_module: Text2SemanticDataModule = Text2SemanticDataModule(
        config,
        train_semantic_path=config["train_semantic_path"],
        train_phoneme_path=config["train_phoneme_path"],
    )
    print(f"训练数据路径验证：{Path(config['train_semantic_path']).exists()}")
    print(f"音素数据路径验证：{Path(config['train_phoneme_path']).exists()}")
    
    try:
        # 使用正则表达式匹配文件名中的数字部分，并按数字大小进行排序
        newest_ckpt_name = get_newest_ckpt(os.listdir(ckpt_dir))
        ckpt_path = ckpt_dir / newest_ckpt_name
    except Exception:
        ckpt_path = None
    trainer.fit(model, data_module, ckpt_path=ckpt_path)
    
   