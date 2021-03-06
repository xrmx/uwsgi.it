from django.contrib import admin
from django.forms import ModelForm,HiddenInput

# Register your models here.
from uwsgi_it_api.models import *

class ServerAdmin(admin.ModelAdmin):
    def memory_status(self):
        return "available:%d used:%d free:%d" % (self.memory, self.used_memory, self.free_memory)
    def storage_status(self):
        return "available:%d used:%d free:%d" % (self.storage, self.used_storage, self.free_storage)
    list_display = ('__unicode__', memory_status, storage_status, 'legion', 'weight', 'owner')
    list_filter = ('legion', 'datacenter')

class ContainerAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContainerAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].queryset = Tag.objects.filter(customer=self.instance.customer)
        else:
            self.fields['tags'].widget = HiddenInput()

class ContainerAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'ip', 'hostname', 'customer', 'server', 'distro', 'memory', 'storage', 'accounted')
    list_filter = ('server', 'distro', 'accounted')
    search_fields = ('name', 'customer__user__username', 'tags__name')

    form = ContainerAdminForm

class DomainAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DomainAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].queryset = Tag.objects.filter(customer=self.instance.customer)
        else:
            self.fields['tags'].widget = HiddenInput()
        

class DomainAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'customer')
    list_filter = ('customer',)
    search_fields = ('name',)

    form = DomainAdminForm

class ContainerMetricAdmin(admin.ModelAdmin):
    list_display = ('container', 'year', 'month', 'day')
    list_filter = ('year', 'month')

class DomainMetricAdmin(admin.ModelAdmin):
    list_display = ('domain', 'container', 'year', 'month', 'day')
    list_filter = ('year', 'month')

class LegionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'note')

class TagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'customer')
    list_filter = ('customer',)
    search_fields = ('name',) 

admin.site.register(Server, ServerAdmin)
admin.site.register(Distro)
admin.site.register(Customer)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Legion, LegionAdmin)
admin.site.register(ContainerLink)
admin.site.register(Datacenter)
admin.site.register(Tag, TagAdmin)
admin.site.register(CustomService)
admin.site.register(CustomerAttribute)

admin.site.register(NetworkRXContainerMetric,ContainerMetricAdmin)
admin.site.register(NetworkTXContainerMetric,ContainerMetricAdmin)
admin.site.register(CPUContainerMetric,ContainerMetricAdmin)
admin.site.register(MemoryContainerMetric,ContainerMetricAdmin)
admin.site.register(IOReadContainerMetric,ContainerMetricAdmin)
admin.site.register(IOWriteContainerMetric,ContainerMetricAdmin)
admin.site.register(QuotaContainerMetric,ContainerMetricAdmin)

admin.site.register(HitsDomainMetric,DomainMetricAdmin)
admin.site.register(NetworkRXDomainMetric,DomainMetricAdmin)
admin.site.register(NetworkTXDomainMetric,DomainMetricAdmin)
