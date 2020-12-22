from argparse import ArgumentParser

import pytorch_lightning as pl
from pytorch_lightning import loggers as pl_loggers

from models import VAE, IWAE, AIWAE, AIS_VAE, ULA_VAE, Stacked_VAE
from utils import make_dataloaders, get_activations, str2bool

if __name__ == '__main__':
    parser = ArgumentParser()
    parser = pl.Trainer.add_argparse_args(parser)
    tb_logger = pl_loggers.TensorBoardLogger('lightning_logs/')
    parser.add_argument("--model", default="Stacked_VAE",
                        choices=["VAE", "IWAE", "AIWAE", "AIS_VAE", "ULA_VAE", "Stacked_VAE"])
    parser.add_argument("--batch_size", default=32, type=int)
    parser.add_argument("--val_batch_size", default=50, type=int)
    parser.add_argument("--hidden_dim", default=64, type=int)
    parser.add_argument("--dataset", default='mnist', choices=['mnist', 'fashionmnist', 'cifar', 'omniglot', 'celeba'])
    parser.add_argument("--num_samples", default=1, type=int)
    parser.add_argument("--act_func", default="leakyrelu",
                        choices=["relu", "leakyrelu", "tanh", "logsigmoid", "logsoftmax", "softplus"])
    parser.add_argument("--net_type", choices=["fc", "conv"], type=str, default="conv")

    parser.add_argument("--K", type=int, default=3)
    parser.add_argument("--n_leapfrogs", type=int, default=3)
    parser.add_argument("--step_size", type=float, default=0.01)
    parser.add_argument("--use_barker", type=str2bool, default=False)
    parser.add_argument("--binarize", type=str2bool, default=False)
    parser.add_argument("--use_transforms", type=str2bool, default=False)

    act_func = get_activations()

    args = parser.parse_args()
    print(args)
    args.gpus = 1

    kwargs = {'num_workers': 20, 'pin_memory': True} if args.gpus else {}
    train_loader, val_loader = make_dataloaders(dataset=args.dataset,
                                                batch_size=args.batch_size,
                                                val_batch_size=args.val_batch_size,
                                                binarize=args.binarize,
                                                **kwargs)
    image_shape = train_loader.dataset.shape_size
    if args.model == "VAE":
        model = VAE(shape=image_shape, act_func=act_func[args.act_func],
                    num_samples=args.num_samples, hidden_dim=args.hidden_dim,
                    net_type=args.net_type, dataset=args.dataset)
    elif args.model == "IWAE":
        model = IWAE(shape=image_shape, act_func=act_func[args.act_func], num_samples=args.num_samples,
                     hidden_dim=args.hidden_dim,
                     name=args.model, net_type=args.net_type, dataset=args.dataset)
    elif args.model == 'AIWAE':
        model = AIWAE(shape=image_shape, step_size=args.step_size, n_leapfrogs=args.n_leapfrogs, K=args.K,
                      use_barker=args.use_barker,
                      act_func=act_func[args.act_func],
                      num_samples=args.num_samples, hidden_dim=args.hidden_dim,
                      name=args.model, net_type=args.net_type, dataset=args.dataset)
    elif args.model == 'AIS_VAE':
        model = AIS_VAE(shape=image_shape, step_size=args.step_size, K=args.K, use_barker=args.use_barker,
                        num_samples=args.num_samples,
                        dataset=args.dataset, net_type=args.net_type, act_func=act_func[args.act_func],
                        hidden_dim=args.hidden_dim, name=args.model)
    elif args.model == 'ULA_VAE':
        model = ULA_VAE(shape=image_shape, step_size=args.step_size, K=args.K,
                        num_samples=args.num_samples,
                        dataset=args.dataset, net_type=args.net_type, act_func=act_func[args.act_func],
                        hidden_dim=args.hidden_dim, name=args.model, use_transforms=args.use_transforms)
    elif args.model == 'Stacked_VAE':
        model = Stacked_VAE(shape=image_shape, act_func=act_func[args.act_func], num_samples=args.num_samples,
                            hidden_dim=args.hidden_dim,
                            name=args.model, net_type=args.net_type, dataset=args.dataset, step_size=args.step_size,
                            K=args.K, use_barker=args.use_barker, n_first_iterations=5, first_model='VAE',
                            second_model='AIS_VAE')
    else:
        raise ValueError

    trainer = pl.Trainer.from_argparse_args(args, logger=tb_logger, fast_dev_run=False)
    pl.Trainer()
    trainer.fit(model, train_dataloader=train_loader, val_dataloaders=val_loader)
