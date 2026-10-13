terraform {
  required_providers { ncloud = { source = "NaverCloudPlatform/ncloud" } }
}
provider "ncloud" { 
  region      = "KR" 
  support_vpc = true
}

# ==========================================
# VPC 1 (prod-vpc) 생성
# ==========================================
resource "ncloud_vpc" "vpc_0" {
  name            = "bgko-prod-vpc"
  ipv4_cidr_block = "10.0.0.0/16"
}

resource "ncloud_subnet" "sub_0_0" {
  vpc_no         = ncloud_vpc.vpc_0.vpc_no  # ★ 파이썬이 자동으로 해당 VPC의 ID를 참조하도록 연결!
  subnet         = "10.0.1.0/24"
  zone           = "KR-1"
  network_acl_no = ncloud_vpc.vpc_0.default_network_acl_no
  subnet_type    = "PUBLIC"
  name           = "bgko-prod-vpc-sub1"
  usage_type     = "GEN"
}

resource "ncloud_subnet" "sub_0_1" {
  vpc_no         = ncloud_vpc.vpc_0.vpc_no  # ★ 파이썬이 자동으로 해당 VPC의 ID를 참조하도록 연결!
  subnet         = "10.0.2.0/24"
  zone           = "KR-1"
  network_acl_no = ncloud_vpc.vpc_0.default_network_acl_no
  subnet_type    = "PRIVATE"
  name           = "bgko-prod-vpc-sub2"
  usage_type     = "GEN"
}

# ==========================================
# VPC 2 (dev-vpc) 생성
# ==========================================
resource "ncloud_vpc" "vpc_1" {
  name            = "bgko-dev-vpc"
  ipv4_cidr_block = "192.168.0.0/16"
}

resource "ncloud_subnet" "sub_1_0" {
  vpc_no         = ncloud_vpc.vpc_1.vpc_no  # ★ 파이썬이 자동으로 해당 VPC의 ID를 참조하도록 연결!
  subnet         = "192.168.1.0/24"
  zone           = "KR-2"
  network_acl_no = ncloud_vpc.vpc_1.default_network_acl_no
  subnet_type    = "PRIVATE"
  name           = "bgko-dev-vpc-sub1"
  usage_type     = "GEN"
}

resource "ncloud_subnet" "sub_1_1" {
  vpc_no         = ncloud_vpc.vpc_1.vpc_no  # ★ 파이썬이 자동으로 해당 VPC의 ID를 참조하도록 연결!
  subnet         = "192.168.2.0/24"
  zone           = "KR-2"
  network_acl_no = ncloud_vpc.vpc_1.default_network_acl_no
  subnet_type    = "PUBLIC"
  name           = "bgko-dev-vpc-sub2"
  usage_type     = "GEN"
}

# ==========================================
# VPC 3 (vpc-3) 생성
# ==========================================
resource "ncloud_vpc" "vpc_2" {
  name            = "bgko-vpc-3"
  ipv4_cidr_block = "10.0.0.0/16"
}

resource "ncloud_subnet" "sub_2_0" {
  vpc_no         = ncloud_vpc.vpc_2.vpc_no  # ★ 파이썬이 자동으로 해당 VPC의 ID를 참조하도록 연결!
  subnet         = "10.0.1.0/24"
  zone           = "KR-1"
  network_acl_no = ncloud_vpc.vpc_2.default_network_acl_no
  subnet_type    = "PUBLIC"
  name           = "bgko-vpc-3-sub1"
  usage_type     = "GEN"
}
