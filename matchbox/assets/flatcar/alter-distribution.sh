#!/usr/bin/env bash

set -ex

test $(id -u -r) -eq 0
test ${VERSION}
test ${COMMIT_ID}

cd $(dirname $0)
FLATCAR_DIRECTORY=$(pwd -P)
ASSETS_DIRECTORY=$(dirname ${FLATCAR_DIRECTORY})
export VERSION_DIR=${FLATCAR_DIRECTORY}/${VERSION}

cd ${VERSION_DIR}
export USR_A=${VERSION_DIR}/usr-a
export ROOTFS=${VERSION_DIR}/rootfs
export BOOT=${VERSION_DIR}/boot
export VERSION

mkdir -pv {squashfs,initrd} ${USR_A} ${BOOT} ${ROOTFS}

bzip2 -fdk flatcar_production_image.bin.bz2
${FLATCAR_DIRECTORY}/disk.py rw

LOOP=$(losetup --find --show flatcar_production_image.bin)
partprobe ${LOOP}

set +e
umount ${LOOP}p9 ${ROOTFS}
umount ${LOOP}p3 ${USR_A}
umount ${LOOP}p1 ${BOOT}
set -e

mount ${LOOP}p9 ${ROOTFS}
mount ${LOOP}p3 ${USR_A}
mount ${LOOP}p1 ${BOOT}
gunzip -c --force flatcar_production_pxe_image.cpio.gz > flatcar_production_pxe_image.cpio
cd initrd
cpio -id < ../flatcar_production_pxe_image.cpio
cd ../squashfs
unsquashfs -no-progress ../initrd/usr.squashfs

_remove_in_fs(){
    for fs in squashfs-root/ ${USR_A}
    do
        rm -fv ${fs}/${1}
    done
}

_upx_in_fs() {
    for fs in squashfs-root/ ${USR_A}
    do
        upx -q ${fs}/${1}
        upx -t ${fs}/${1}
    done
}

# CWD == ~/matchbox/assets/flatcar/${VERSION}/squashfs

EXCLUDES="--exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp --exclude rootfs/run --exclude rootfs/sys"

for useless in /bin/docker /bin/containerd /bin/containerd-shim /bin/dockerd /bin/runc \
    /bin/docker-containerd-shim /bin/docker-containerd /bin/docker-runc /bin/ctr /bin/docker-proxy /bin/mayday \
    /bin/actool /bin/tpmd
do
    _remove_in_fs ${useless}
done


HAPROXY_ACI=$(ls ${ACI_PATH}/haproxy/haproxy-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${HAPROXY_ACI} rootfs/usr/sbin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${HAPROXY_ACI} rootfs/usr/sbin --strip 2 ${EXCLUDES}


_remove_in_fs /bin/etcd2
_remove_in_fs /bin/etcdctl
ETCD_ACI=$(ls ${ACI_PATH}/etcd/etcd-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


VAULT_ACI=$(ls ${ACI_PATH}/vault/vault-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}


_remove_in_fs /bin/ip
IPROUTE2_ACI=$(ls ${ACI_PATH}/iproute2/iproute2-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


_remove_in_fs /bin/fleetd
_remove_in_fs /bin/fleetctl
FLEET_ACI=$(ls ${ACI_PATH}/fleet/fleet-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


_remove_in_fs /bin/rkt /lib64/rkt/stage1-images/stage1-fly.aci /lib64/rkt/stage1-images/stage1-coreos.aci
RKT_ACI=$(ls ${ACI_PATH}/rkt/rkt-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}


mkdir -pv squashfs-root/local/cni
mkdir -pv ${USR_A}/local/cni
CNI_ACI=$(ls ${ACI_PATH}/cni/cni-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/local/cni -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
tar -C ${USR_A}/local/cni -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
for p in squashfs-root/bin ${USR_A}/bin
do
    cd ${p}
    ln -svf ../local/cni/bin/cnitool
    cd -
done

HYPERKUBE_ACI=$(ls ${ACI_PATH}/hyperkube/hyperkube-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}
tar -C ${USR_A}/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}

cp -v ${ASSETS_DIRECTORY}/enjoliver-agent/serve/enjoliver-agent squashfs-root/bin/
cp -v ${ASSETS_DIRECTORY}/enjoliver-agent/serve/enjoliver-agent ${USR_A}/bin
_upx_in_fs /bin/enjoliver-agent

cp -v ${ASSETS_DIRECTORY}/discoveryC/serve/discoveryC squashfs-root/bin
cp -v ${ASSETS_DIRECTORY}/discoveryC/serve/discoveryC ${USR_A}/bin
_upx_in_fs /bin/discoveryC

SOCAT_ACI=$(ls ${ACI_PATH}/socat/socat-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root -xvf ${SOCAT_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A} -xvf ${SOCAT_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

for b in /bin/locksmithctl /bin/flatcar-cloudinit
do
    _upx_in_fs ${b}
done

mkdir -pv ${USR_A}/local/etc/ squashfs-root/local/etc/
echo -n "{\"release\": \"${VERSION}\", \"alter_timestamp\": \"$(date +%s)\", \"commit\": \"${COMMIT_ID}\"}" | \
    tee ${USR_A}/local/etc/alter-version squashfs-root/local/etc/alter-version ${VERSION_DIR}/alter-version


# Cloud requirements

mkdir -pv ${ROOTFS}/etc/systemd/system/multi-user.target.wants ${ROOTFS}/etc/systemd/system/multi-user.target.requires

cp -v ${FLATCAR_DIRECTORY}/oem-cloudinit.service ${ROOTFS}/etc/systemd/system/oem-cloudinit.service
cd ${ROOTFS}/etc/systemd/system/multi-user.target.wants
ln -svf /etc/systemd/system/oem-cloudinit.service oem-cloudinit.service
cd -

cp -v ${FLATCAR_DIRECTORY}/flatcar-metadata-sshkeys@.service ${ROOTFS}/etc/systemd/system/flatcar-metadata-sshkeys@.service
cd ${ROOTFS}/etc/systemd/system/multi-user.target.requires
ln -svf /etc/systemd/system/flatcar-metadata-sshkeys@.service flatcar-metadata-sshkeys@core.service
cd -

sync

umount ${ROOTFS}

umount ${USR_A}
${FLATCAR_DIRECTORY}/disk_util --disk_layout=base verity --root_hash=${VERSION_DIR}/flatcar_production_image_verity.txt ${VERSION_DIR}/flatcar_production_image.bin
printf %s "$(cat ${VERSION_DIR}/flatcar_production_image_verity.txt)" | \
        dd of=${BOOT}/flatcar/vmlinuz-a conv=notrunc seek=64 count=64 bs=1 status=none
sync

umount ${BOOT}
losetup -d ${LOOP}

${FLATCAR_DIRECTORY}/disk.py ro
bzip2 -fzk ${VERSION_DIR}/flatcar_production_image.bin -9

cp -v ${FLATCAR_DIRECTORY}/flatcar-install squashfs-root/bin/flatcar-install

mksquashfs squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments
cd ../initrd
find . | cpio -o -H newc | gzip -9 > ../flatcar_production_pxe_image.cpio.gz
cd ../

rm -rf squashfs initrd flatcar_production_pxe_image.cpio ${USR_A}
