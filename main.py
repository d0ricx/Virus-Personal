import ctypes
import subprocess
import os
import sys
import platform
import time
import wmi

def ensure_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000

def create_executable_buffer(machine_code: bytes):
    buf = ctypes.windll.kernel32.VirtualAlloc(
        None,
        len(machine_code),
        MEM_COMMIT | MEM_RESERVE,
        PAGE_EXECUTE_READWRITE
    )
    if not buf:
        raise OSError("VirtualAlloc failed")

    ctypes.memmove(buf, machine_code, len(machine_code))
    return buf

def cpuid(eax_input: int):
    shellcode = bytes([
        0x53,                   # push rbx
        0x49, 0x89, 0xC8,       # mov r8, rcx
        0x89, 0xC8,             # mov eax, ecx
        0x0F, 0xA2,             # cpuid
        0x41, 0x89, 0x00,       # mov [r8], eax
        0x41, 0x89, 0x58, 0x04, # mov [r8+4], ebx
        0x41, 0x89, 0x48, 0x08, # mov [r8+8], ecx
        0x41, 0x89, 0x50, 0x0C, # mov [r8+12], edx
        0x5B,                   # pop rbx
        0xC3                    # ret
    ])

    func_ptr = create_executable_buffer(shellcode)
    func_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_uint32))
    func = func_type(func_ptr)

    out = (ctypes.c_uint32 * 4)()
    out[0] = eax_input
    func(out)
    return out[0], out[1], out[2], out[3]

class VMDetector:
    def __init__(self):
        self.score = 0
        self.w = wmi.WMI()

    def check_hypervisor_bit(self):
        try:
            eax, ebx, ecx, edx = cpuid(1)
            if ecx & (1 << 31):
                self.score += 25
                return True
        except:
            pass
        return False

    def check_hypervisor_vendor(self):
        try:
            _, b, c, d = cpuid(0x40000000)
            vendor = "".join([
                chr((x >> i) & 0xFF) for x in (0, 8, 16, 24) for x in [b, c, d]
            ])
            known = [
                "VMwareVMware",
                "VBoxVBoxVBox",
                "Microsoft Hv",
                "KVMKVMKVM",
                "XenVMMXenVMM",
                "prl hyperv"
            ]
            if any(k in vendor for k in known):
                self.score += 30
                return True
        except:
            pass
        return False

    def check_bios_vendor(self):
        try:
            vendor = self.w.Win32_BIOS()[0].Manufacturer.lower()
            suspicious = [
                "vmware",
                "vbox",
                "virtualbox",
                "qemu",
                "bochs",
                "xen",
                "hyper-v"
            ]
            if any(s in vendor for s in suspicious):
                self.score += 20
                return True
        except:
            pass
        return False

    def check_disk_vendor(self):
        try:
            for disk in self.w.Win32_DiskDrive():
                model = disk.Model.lower()
                suspicious = [
                    "vbox",
                    "virtual",
                    "vmware",
                    "qemu",
                    "hyper-v"
                ]
                if any(s in model for s in suspicious):
                    self.score += 25
                    return True
        except:
            pass
        return False

    def check_gpu(self):
        try:
            for gpu in self.w.Win32_VideoController():
                name = gpu.Name.lower()
                if "vmware" in name or "virtual" in name or "qxl" in name:
                    self.score += 15
                    return True
        except:
            pass
        return False

    def check_mac(self):
        prefixes = [
            "00:05:69",
            "00:0C:29",
            "00:1C:14",
            "00:50:56",
            "08:00:27",
            "00:16:3E",
            "52:54:00"
        ]
        try:
            output = subprocess.check_output("getmac", shell=True).decode().lower()
            if any(p.lower() in output for p in prefixes):
                self.score += 20
                return True
        except:
            pass
        return False

    def check_processes(self):
        vm_procs = [
            "vmtoolsd",
            "vmwaretray",
            "vboxservice",
            "vboxtray",
            "qemu-ga",
            "xenservice"
        ]
        try:
            running = subprocess.check_output("tasklist", shell=True).decode().lower()
            if any(p in running for p in vm_procs):
                self.score += 20
                return True
        except:
            pass
        return False

    def timing_check(self):
        t1 = time.perf_counter()
        for _ in range(5000000):
            pass
        t2 = time.perf_counter()
        if t2 - t1 > 0.25:
            self.score += 10
            return True
        return False

    def detect(self):
        self.check_hypervisor_bit()
        self.check_hypervisor_vendor()
        self.check_bios_vendor()
        self.check_disk_vendor()
        self.check_gpu()
        self.check_mac()
        self.check_processes()
        self.timing_check()
        return self.score >= 40

if __name__ == "__main__":
    ensure_admin()
    detector = VMDetector()

    if detector.detect():
        print("VM DETECTED")
    else:
        print("REAL MACHINE")
