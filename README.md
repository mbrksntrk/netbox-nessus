# Netbox-Nessus Integration Tool

Bu Python uygulaması, Nessus vulnerability scanner ile Netbox network infrastructure management sistemini entegre eder.

## Özellikler

### Nessus Entegrasyonu
- Nessus API'sına bağlanma ve kimlik doğrulama
- Tüm agent'ları listeleme ve detaylı bilgi çekme
- Agent'ları durum ve platforma göre filtreleme
- Scan sonuçlarını çekme
- Agent istatistikleri oluşturma

### Netbox Entegrasyonu
- Netbox API'sına bağlanma ve kimlik doğrulama
- Cihazları listeleme ve yönetme
- Site ve duruma göre cihaz filtreleme
- IP adreslerini yönetme
- Cihaz istatistikleri oluşturma

### Entegrasyon Özellikleri
- Nessus agent'larını Netbox cihazlarına senkronize etme
- Otomatik cihaz oluşturma ve güncelleme
- JSON formatında veri kaydetme
- Modüler ve genişletilebilir yapı

## Proje Yapısı

```
netbox-nessus/
├── api/                    # API Client'ları
│   ├── __init__.py
│   ├── base_client.py      # Temel API client sınıfı
│   ├── nessus_client.py    # Nessus API client
│   └── netbox_client.py    # Netbox API client
├── config/                 # Konfigürasyon
│   ├── __init__.py
│   ├── settings.py         # Konfigürasyon yönetimi
│   └── config.json.example # Örnek konfigürasyon
├── services/               # İş mantığı katmanı
│   ├── __init__.py
│   ├── nessus_service.py   # Nessus işlemleri
│   └── netbox_service.py   # Netbox işlemleri
├── utils/                  # Yardımcı fonksiyonlar
│   ├── __init__.py
│   └── helpers.py          # Ortak yardımcı fonksiyonlar
├── models/                 # Veri modelleri
│   └── __init__.py
├── output/                 # Çıktı dosyaları
├── logs/                   # Log dosyaları
├── main.py                 # Ana uygulama
├── main_old.py             # Eski main dosyası (yedek)
├── requirements.txt        # Python bağımlılıkları
└── README.md              # Bu dosya
```

## Kurulum

1. **Virtual Environment Oluşturun:**
```bash
python -m venv venv
```

2. **Virtual Environment'ı Aktifleştirin:**
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

3. **Gerekli Paketleri Yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Konfigürasyon Dosyasını Oluşturun:**
```bash
cp config/config.json.example config/config.json
```

5. **Konfigürasyon Dosyasını Düzenleyin:**
```json
{
  "nessus": {
    "base_url": "https://your-nessus-server:8834",
    "access_key": "your-access-key",
    "secret_key": "your-secret-key",
    "verify_ssl": false
  },
  "netbox": {
    "base_url": "https://your-netbox-server",
    "token": "your-netbox-token",
    "verify_ssl": false
  },
  "output": {
    "file": "output/data.json",
    "format": "json"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  }
}
```

## Kullanım

### Ana Uygulamayı Çalıştırma
```bash
python main.py
```

Uygulama interaktif bir menü sunar:

1. **Fetch Nessus Agents** - Nessus'tan agent'ları çeker
2. **Fetch Netbox Devices** - Netbox'tan cihazları çeker
3. **Sync Nessus Agents to Netbox** - Agent'ları Netbox'a senkronize eder
4. **Exit** - Uygulamadan çıkış

### Environment Variables ile Kullanım

```bash
# Windows PowerShell
$env:NESSUS_URL="https://your-nessus-server:8834"
$env:NESSUS_ACCESS_KEY="your-access-key"
$env:NESSUS_SECRET_KEY="your-secret-key"
$env:NETBOX_URL="https://your-netbox-server"
$env:NETBOX_TOKEN="your-netbox-token"
python main.py

# Linux/Mac
export NESSUS_URL="https://your-nessus-server:8834"
export NESSUS_ACCESS_KEY="your-access-key"
export NESSUS_SECRET_KEY="your-secret-key"
export NETBOX_URL="https://your-netbox-server"
export NETBOX_TOKEN="your-netbox-token"
python main.py
```

## API Anahtarlarını Alma

### Nessus API Anahtarları
1. Nessus web arayüzüne giriş yapın
2. **Settings** > **My Account** bölümüne gidin
3. **API Keys** sekmesine tıklayın
4. **Generate** butonuna tıklayarak yeni anahtarlar oluşturun

### Netbox API Token
1. Netbox web arayüzüne giriş yapın
2. **Admin** > **Users** bölümüne gidin
3. Kullanıcınızı seçin
4. **API Tokens** sekmesine tıklayın
5. **Add API Token** butonuna tıklayın

## Çıktı Formatları

### Agent Verileri
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "data_type": "agents",
  "total_count": 5,
  "data": [
    {
      "id": 1,
      "name": "Agent-001",
      "status": "online",
      "platform": "Windows",
      "version": "10.5.0",
      "last_connect": "2024-01-15T10:25:00Z",
      "groups": ["Windows Agents"],
      "distro": "Windows 10",
      "uuid": "12345678-1234-1234-1234-123456789012"
    }
  ]
}
```

### Cihaz Verileri
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "data_type": "devices",
  "total_count": 3,
  "data": [
    {
      "id": 1,
      "name": "Server-001",
      "status": {"value": "active"},
      "site": {"name": "Main Site"},
      "device_type": {"model": "Dell PowerEdge"},
      "platform": {"name": "Windows Server 2019"}
    }
  ]
}
```

## Modüler Yapı Avantajları

### API Katmanı (`api/`)
- **base_client.py**: Ortak HTTP işlemleri ve hata yönetimi
- **nessus_client.py**: Nessus API'sına özel işlemler
- **netbox_client.py**: Netbox API'sına özel işlemler

### Servis Katmanı (`services/`)
- **nessus_service.py**: Nessus iş mantığı ve veri işleme
- **netbox_service.py**: Netbox iş mantığı ve veri işleme

### Konfigürasyon (`config/`)
- **settings.py**: Merkezi konfigürasyon yönetimi
- Environment variables ve dosya desteği
- Konfigürasyon doğrulama

### Yardımcı Fonksiyonlar (`utils/`)
- **helpers.py**: Ortak yardımcı fonksiyonlar
- JSON dosya işlemleri
- Veri formatlama ve filtreleme

## Hata Yönetimi

Uygulama aşağıdaki durumları yönetir:
- Bağlantı hataları
- Kimlik doğrulama hataları
- JSON parse hataları
- Dosya yazma hataları
- SSL sertifika hataları
- API rate limiting

## Güvenlik Notları

- API anahtarlarınızı güvenli tutun
- `config/config.json` dosyasını version control'e eklemeyin
- Production ortamında SSL doğrulamasını etkinleştirin
- API anahtarlarını düzenli olarak yenileyin
- Virtual environment kullanın

## Geliştirme

### Yeni API Ekleme
1. `api/` klasöründe yeni client oluşturun
2. `BaseAPIClient`'dan inherit edin
3. `services/` klasöründe service oluşturun
4. `config/settings.py`'de konfigürasyon ekleyin

### Yeni Özellik Ekleme
1. İlgili service dosyasında metod ekleyin
2. `main.py`'de menü seçeneği ekleyin
3. Gerekirse yardımcı fonksiyonlar ekleyin

## Sorun Giderme

### Bağlantı Hataları
- URL'leri kontrol edin
- Firewall ayarlarını kontrol edin
- SSL sertifika ayarlarını kontrol edin

### Kimlik Doğrulama Hataları
- API anahtarlarının doğru olduğunu kontrol edin
- API anahtarlarının süresi dolmuş olabilir

### Import Hataları
- Virtual environment'ın aktif olduğunu kontrol edin
- Gerekli paketlerin yüklü olduğunu kontrol edin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 