provider "aws" { region = var.aws_region }
resource "aws_security_group" "k8s_sg" { name="k8s-sg"
 ingress {from_port=22 to_port=22 protocol="tcp" cidr_blocks=["0.0.0.0/0"]}
 ingress {from_port=6443 to_port=6443 protocol="tcp" cidr_blocks=["0.0.0.0/0"]}
 egress {from_port=0 to_port=0 protocol="-1" cidr_blocks=["0.0.0.0/0"]}}
resource "aws_instance" "master" { ami=var.ami_id instance_type="t3.medium" key_name=var.key_name vpc_security_group_ids=[aws_security_group.k8s_sg.id] tags={Name="k8s-master"}}
resource "aws_instance" "worker" { ami=var.ami_id instance_type="t3.medium" key_name=var.key_name vpc_security_group_ids=[aws_security_group.k8s_sg.id] tags={Name="k8s-worker"}}
