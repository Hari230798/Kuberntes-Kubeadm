pipeline {

    agent {
        label 'jenkins-worker01'
    }

    stages {

        stage('Terraform Validate') {
            steps {
                sh 'cd terraform && terraform fmt -check'
                sh 'cd terraform && terraform validate'
            }
        }

        stage('Terraform Init') {
            steps {
                sh 'cd terraform && terraform init'
            }
        }

        stage('Terraform Plan') {
            steps {
                sh 'cd terraform && terraform plan -out=tfplan'
            }
        }

        stage('Terraform Apply') {
            steps {
                sh 'cd terraform && terraform apply -auto-approve tfplan'
            }
        }

        stage('Configure Cluster') {
            steps {
                sh 'ansible-playbook -i ansible/inventory.ini ansible/common.yml'
                sh 'ansible-playbook -i ansible/inventory.ini ansible/kube-master.yml'
                sh 'ansible-playbook -i ansible/inventory.ini ansible/kube-worker.yml'
                sh 'ansible-playbook -i ansible/inventory.ini ansible/calico.yml'
            }
        }
    }
}
