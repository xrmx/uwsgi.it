from django.db import models
from django.contrib.auth.models import User
import calendar
import ipaddress
import uuid
from django.core.exceptions import ValidationError
import string
from Crypto.PublicKey import RSA
from uwsgi_it_api.config import UWSGI_IT_BASE_UID


# Create your models here.

generate_uuid = lambda: str(uuid.uuid4())

def generate_rsa():
    return RSA.generate(2048).exportKey()

class Customer(models.Model):
    user = models.OneToOneField(User)
    vat = models.CharField(max_length=255,blank=True,null=True)
    company = models.CharField(max_length=255,blank=True,null=True)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    rsa_key = models.TextField(default=generate_rsa, unique=True)

    @property
    def rsa_key_lines(self):
        return self.rsa_key.split('\n')

    @property
    def rsa_pubkey(self):
        return RSA.importKey(self.rsa_key).publickey().exportKey()

    @property
    def rsa_pubkey_lines(self):
        return self.rsa_pubkey.split('\n')

    def __unicode__(self):
        return self.user.username

class Server(models.Model):
    name = models.CharField(max_length=255,unique=True)
    address = models.GenericIPAddressField()

    hd = models.CharField(max_length=255)

    memory = models.PositiveIntegerField("Memory MB")
    storage = models.PositiveIntegerField("Storage MB")

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    @property
    def used_memory(self):
        n = self.container_set.all().aggregate(models.Sum('memory'))['memory__sum']
        if not n: return 0
        return n

    @property
    def used_storage(self):
        n = self.container_set.all().aggregate(models.Sum('storage'))['storage__sum']
        if not n: return 0
        return n

    @property
    def free_memory(self):
        return self.memory - self.used_memory

    @property
    def free_storage(self):
        return self.storage - self.used_storage

    def __unicode__(self):
        return "%s - %s" % (self.name, self.address)

class Distro(models.Model):
    name = models.CharField(max_length=255,unique=True)
    path = models.CharField(max_length=255,unique=True)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    def __unicode__(self):
        return self.name

class Container(models.Model):
    name = models.CharField(max_length=255)
    ssh_keys_raw = models.TextField("SSH keys", blank=True,null=True)
    distro = models.ForeignKey(Distro)
    server = models.ForeignKey(Server)
    # in megabytes
    memory = models.PositiveIntegerField("Memory MB")
    storage = models.PositiveIntegerField("Storage MB")
    customer = models.ForeignKey(Customer)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    note = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return "%d (%s)" % (self.uid, self.name)

    # do not allow over-allocate memory or storage
    def clean(self):
        current_storage = self.server.container_set.all().aggregate(models.Sum('storage'))['storage__sum']
        current_memory = self.server.container_set.all().aggregate(models.Sum('memory'))['memory__sum']
        if not current_storage: current_storage = 0
        if not current_memory: current_memory = 0
        if self.pk:
            orig = Container.objects.get(pk=self.pk)
            current_storage -= orig.storage
            current_memory -= orig.memory
        if current_storage+self.storage > self.server.storage:
            raise ValidationError('the requested storage size is not available on the specified server')
        if current_memory+self.memory > self.server.memory:
            raise ValidationError('the requested memory size is not available on the specified server')
        

    @property
    def uid(self):
        return UWSGI_IT_BASE_UID+self.pk

    @property
    def hostname(self):
        h = ''
        allowed = string.ascii_letters + string.digits + '.-'
        for char in self.name:
            if char in allowed:
                h += char
            else:
                h += '-'
        return h

    @property
    def ip(self):
        # skip the first two addresses (10.0.0.1 for the gateway, 10.0.0.2 for the api)
        addr = self.pk + 2
        addr0 = 0x0a000000;
        return ipaddress.IPv4Address(addr0 | (addr & 0x00ffffff))

    @property
    def munix(self):
        return calendar.timegm(self.mtime.utctimetuple())

    @property
    def ssh_keys(self):
        # try to generate a clean list of ssh keys
        cleaned = self.ssh_keys_raw.replace('\r', '\n').replace('\n\n', '\n')
        return self.ssh_keys_raw.split('\n')

    @property
    def quota(self):
        return self.storage * (1024*1024)

    @property
    def memory_limit_in_bytes(self):
        return self.memory * (1024*1024)

"""
domains are mapped to customers, each container of the customer
can subscribe to them
"""
class Domain(models.Model):
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid,unique=True)

    def __unicode__(self):
        return self.name
