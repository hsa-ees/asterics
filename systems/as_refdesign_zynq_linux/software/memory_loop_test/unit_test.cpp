#include <boost/algorithm/hex.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/test/unit_test.hpp>
#include <boost/uuid/detail/md5.hpp>
extern "C" {
#include "asterics.h"
#include "as_invert.h"
}
#include <stdio.h>
#include <sys/mman.h>
#include <iostream>
#include <chrono>
#include <fstream>
using namespace boost::unit_test;
using namespace boost::uuids::detail;

BOOST_AUTO_TEST_SUITE(memory_loop_suite)

struct Image {
  char *ptr = 0;
  int image_size = 0;
};
/** Class containing field and function declarations used to operate every reader/writer module */
class cMemRW {
public:
  cMemRW(const std::string &a_Path, int a_BaseAddr): path(a_Path) {
    is_open = false;
    base_addr = a_BaseAddr;
  };

  Image *GetImage() {
    return &image;
  }

  void SetImageSize(int image_size) {
    image.image_size = image_size;
  }

  bool GetIsOpen() {
    return is_open;
  }

  bool IsTransferComplete() {
    if (data_amount >= image.image_size)
      return true;
    return false;
  }

  virtual void StartTransfer() = 0;

  virtual void Open() = 0;
  virtual void Close() = 0;

protected:
  const std::string path;
  int fd = -1;
  as_hardware_address_t base_addr;
  bool is_open;
  Image image;
  bool is_writer = false;
  size_t data_amount;
};

struct Utilities {
  template <class Module>
  static bool ReadOnce(Module &module) {
    uint32_t n = 0;
    n = read(module.fd, (void *)(module.image.ptr + module.data_amount), module.image.image_size - module.data_amount);
    if (n == -1) {
      n = 0;
      if (errno != EAGAIN) {
        printf("Error writing data to device: %s\n", strerror(errno));
        return false;
      }
    }
    module.data_amount += n;
    return true;
  }
  template <class Module>
  static void Read(Module &module) {
    while (module.data_amount < module.image.image_size) {
      bool bSuccess = ReadOnce(module);
      if (!bSuccess)
        break;
    }
  };
  // MemReader utilities
  template <class Module>
  static bool WriteOnce(Module &module) {
    uint32_t n = 0;
    n = write(module.fd, (void *)(module.image.ptr + module.data_amount), module.image.image_size - module.data_amount);
    if (n == -1) {
      n = 0;
      if (errno != EAGAIN) {
        printf("Error writing data to device: %s\n", strerror(errno));
        return false;
      }
    }
    module.data_amount += n;
    return true;
  }
  template <class Module>
  static void Write(Module &module) {
    while (module.data_amount < module.image.image_size) {
      bool bSuccess = WriteOnce(module);
      if (!bSuccess)
        break;
    }
  };

  // File utilities
  template <class Module>
  static bool OpenFile(Module &module, int flag) {
    module.fd = open(module.path.c_str(), flag);
    if (module.fd == -1) {
      module.is_open = false;
      std::cerr << "Failed to open " << module.path << std::endl;
      return false;
    }
    return true;
  };

  template <class Module>
  static void CloseFile(Module &module) {
    if (module.fd >= 0) {
      close(module.fd);
      module.is_open = false;
    }
    module.fd = -1;
  };

  /** Allocate Images for use in mmap read/write */
  template <class Module>
  static bool AllocateImageMmap(Module &module) {
    void *ptr = mmap(NULL, module.image.image_size, PROT_READ | PROT_WRITE, MAP_SHARED, module.fd, 0);
    if (ptr == MAP_FAILED) {
      module.is_open = false;
      std::cerr << "Failed to map" << std::endl;
      return false;
    }
    module.image.ptr = static_cast<char *>(ptr);
    return true;
  }

  /** Free Images for use in mmap read/write */
  template <class Module>
  static bool FreeImageMmap(Module &module) {
    int ret = munmap(module.image.ptr, module.image.image_size);
    module.image.ptr = nullptr;
    assert(ret == 0);
    return (ret == 0);
  }

  /** Allocate Images for use in "normal" read/write */
  template <class Module>
  static bool AllocateImage(Module &module) {
    module.image.ptr = new char[module.image.image_size];
    if (!module.image.ptr) {
      std::cerr << "Couldn't allocate image" << std::endl;
      return false;
    }
    return true;
  }

  /** Free Images for use in "normal" read/write */
  template <class Module>
  static bool FreeImage(Module &module) {
    if (module.image.ptr)
      delete[] module.image.ptr;
    else
      return false;

    return true;
  }
};

class cMemReaderMmap : public cMemRW {
 public:
  // using cMemReader::cMemReader;
  cMemReaderMmap(const std::string &a_Path, int a_BaseAddr) : cMemRW(a_Path, a_BaseAddr) {}
  ~cMemReaderMmap() { Close(); }

  friend Utilities;
  /** Starts transfer for mmap devices */
  virtual void StartTransfer() override {
    as_ioctl_params_t memreader_args;
    // Legacy way non-blocking
    memreader_args.cmd = AS_IOCTL_CMD_WRITE;
    memreader_args.value = image.image_size;
    memreader_args.address = base_addr;
    memreader_args.user_addr_start = 0;

    if (ioctl(fd, CALLED_FROM_USER, &memreader_args) != 0) {
      perror("ERROR: ioctl() to memreader failed");
    }
  }

  /** Needs to be called only when ioctl used to start transfer
   * No point in using when read/write as 0 indicates transfer is finished */
  virtual void WaitForCompletion() {
    as_ioctl_params_t memreader_args;

    memreader_args.cmd = AS_IOCTL_CMD_MMAP_WAIT;
    memreader_args.address = base_addr;

    //printf("Going to for completion at address: %x\n", base_addr);
    if(ioctl(fd, CALLED_FROM_USER, &memreader_args) != 0)
    {
        perror("ERROR: ioctl() to memreader failed");
    }
  }

  virtual void Open() override {
    if(!Utilities::OpenFile(*this, O_RDWR))
      return;

    if (Utilities::AllocateImageMmap(*this))
      is_open = true;
    else
      Utilities::CloseFile(*this);
  }

  virtual void Close() override {
    Utilities::FreeImageMmap(*this);
    Utilities::CloseFile(*this);
  }
};
/** Blocking write with mmap */
class cMemReaderMmapWrite : public cMemRW {
 public:
  cMemReaderMmapWrite(const std::string &a_Path, int a_BaseAddr) : cMemRW(a_Path, a_BaseAddr) {}
  ~cMemReaderMmapWrite() { Close(); }

  friend Utilities;
  /** Starts transfer for mmap devices */
  virtual void StartTransfer() override {
    data_amount = 0;
    // WriteOnce if non-blocking else Write
    Utilities::Write(*this);
  }

  /** Needs to be called only when ioctl used to start transfer
   * No point in using when read/write as 0 indicates transfer is finished */
  virtual void WaitForCompletion() {
    Utilities::Write(*this);
  }

  virtual void Open() override {
    if(!Utilities::OpenFile(*this, O_RDWR))
      return;

    if (Utilities::AllocateImageMmap(*this))
      is_open = true;
    else
      Utilities::CloseFile(*this);
  }

  virtual void Close() override {
    Utilities::FreeImageMmap(*this);
    Utilities::CloseFile(*this);
  }
};
/** Non-blocking write without mmap */
class cMemReaderWrite : public cMemRW {
 public:
  cMemReaderWrite(const std::string &a_Path, int a_BaseAddr) : cMemRW(a_Path, a_BaseAddr) {}
  ~cMemReaderWrite() { Close(); }

  friend Utilities;
  virtual void StartTransfer() override {
    data_amount = 0;
    Utilities::WriteOnce(*this);
  }

  virtual void Open() override {
    if (!Utilities::OpenFile(*this, O_WRONLY | O_NONBLOCK))
      return;

    if(!Utilities::AllocateImage(*this)) {
      Utilities::CloseFile(*this);
      return;
    }

    is_open = true;
  }

  virtual void Close() override {
    Utilities::CloseFile(*this);
    Utilities::FreeImage(*this);
  }

  virtual void WaitForCompletion() {
    Utilities::Write(*this);
  }
};
/** Non-blocking read with mmap */
class cMemWriterMmapRead : public cMemRW {
 public:
  cMemWriterMmapRead(const std::string &a_Path, int a_BaseAddr) : cMemRW(a_Path, a_BaseAddr) {
    is_writer = true;
  }
  ~cMemWriterMmapRead() { Close(); }

  friend Utilities;

  virtual void StartTransfer() override {
    assert(image.ptr);
    data_amount = 0;
    Utilities::ReadOnce(*this);
  }

  virtual void Open() override {
    if(!Utilities::OpenFile(*this, O_RDWR | O_NONBLOCK))
      return;

    if (Utilities::AllocateImageMmap(*this))
      is_open = true;
    else
      Utilities::CloseFile(*this);
  }

  virtual void Close() override {
    Utilities::CloseFile(*this);
    Utilities::FreeImageMmap(*this);
  }

  virtual void WaitForCompletion() {
    Utilities::Read(*this);
  }
};
/** Non-blocking read without mmap */
class cMemWriterRead : public cMemRW {
 public:
  cMemWriterRead(const std::string &a_Path, int a_BaseAddr) : cMemRW(a_Path, a_BaseAddr) {
    is_writer = true;
  }
  ~cMemWriterRead() { Close(); }

  friend Utilities;

  virtual void StartTransfer() override {
    assert(image.ptr);
    data_amount = 0;
    Utilities::ReadOnce(*this);
  }

  virtual void Open() override {
    if (!Utilities::OpenFile(*this, O_RDONLY | O_NONBLOCK))
      return;

    if (!Utilities::AllocateImage(*this)) {
      Utilities::CloseFile(*this);
      return;
    }

    is_open = true;
  }

  virtual void Close() override {
    Utilities::CloseFile(*this);
    Utilities::FreeImage(*this);
  }

  virtual void WaitForCompletion() {
    Utilities::Read(*this);
  }
};

const std::string input_file = "/home/zynq/input.raw";
const std::string output_file = "/home/zynq/output.raw";

const std::string memwriter_output_read = "/dev/as_memwriter_0_128";
const std::string memwriter_output_mmap = "/dev/as_mmap_0_out_data";
const std::string memreader_input_write = "/dev/as_memreader_0_128";
const std::string memreader_input_mmap = "/dev/as_mmap_0_in_data";

class cTestContext {
  FILE *img_file_fd;
  FILE *output_file_fd;

  bool OpenFiles() {
    img_file_fd = fopen(input_file.c_str(), "rb");
    if(img_file_fd == nullptr)
      return false;
    output_file_fd = fopen(output_file.c_str(), "rb");
    if (output_file_fd == nullptr)
      return false;
  }


};

/** Checks if hash is valid for test data */
bool CheckHash(const Image *img, bool is_inverted = true) {

  const std::string expected_hash_string_invert = "65CCE515095B023F17BCAE2E076322DA";
  const std::string expected_hash_string_no_invert = "3AC62A6F9863EE8A98E2F987571AD160";

  const std::string &expected_hash_string = is_inverted ? expected_hash_string_invert : expected_hash_string_no_invert;

  md5 hash_function;
  md5::digest_type digest;

  hash_function.process_bytes(img->ptr, img->image_size);
  hash_function.get_digest(digest);

  const char *digest_char = reinterpret_cast<const char *>(&digest);
  std::string digest_string;
  boost::algorithm::hex(digest_char, digest_char + 16, std::back_inserter(digest_string));
  std::cout << "Hash was: " << digest_string << std::endl;

  bool is_equal = boost::algorithm::equals(expected_hash_string, digest_string);
  return is_equal;
}

/** Checks for cache problems after toggling invertion */
BOOST_AUTO_TEST_CASE(memory_loop_case_one_invert) {
  // Needed for regio access
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_TRUE);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderMmap memreader_mmap(memreader_input_mmap, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_mmap.GetImage();
  memreader_mmap.SetImageSize(1280*960);
  memreader_mmap.Open();
  BOOST_CHECK(img->ptr);

  cMemWriterRead memwriter_read(memwriter_output_read, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_mmap.StartTransfer();

    memwriter_read.WaitForCompletion();
    memreader_mmap.WaitForCompletion();
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  bool image_correct = CheckHash(img_output);
  if (!image_correct) {
    std::cerr << "Image not expected, saving image" << std::endl;
    output_file_stream.write(img_output->ptr, img_output->image_size);
  }
  BOOST_CHECK(image_correct);
}

/** Checks for cache problems after toggling invertion */
BOOST_AUTO_TEST_CASE(memory_loop_case_one_no_invert) {
  // Needed for regio access
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_FALSE);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderMmap memreader_mmap(memreader_input_mmap, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_mmap.GetImage();
  memreader_mmap.SetImageSize(1280*960);
  memreader_mmap.Open();
  BOOST_CHECK(img->ptr);

  cMemWriterRead memwriter_read(memwriter_output_read, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_mmap.StartTransfer();

    memwriter_read.WaitForCompletion();
    memreader_mmap.WaitForCompletion();
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  bool image_correct = CheckHash(img_output, false);
  if (!image_correct) {
    std::cerr << "Image not expected, saving image" << std::endl;
    output_file_stream.write(img_output->ptr, img_output->image_size);
  }
  BOOST_CHECK(image_correct);
}

/** Tests mmap ioctl write + read */
BOOST_AUTO_TEST_CASE(memory_loop_multiple_mmap_write) {
  // Needed for regio access
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_TRUE);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderMmap memreader_mmap(memreader_input_mmap, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_mmap.GetImage();
  BOOST_CHECK(!img->ptr);
  memreader_mmap.Open();
  BOOST_CHECK(!img->ptr);
  memreader_mmap.SetImageSize(1280*960);
  memreader_mmap.Open();
  BOOST_CHECK(img->ptr);

  cMemWriterRead memwriter_read(memwriter_output_read, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  BOOST_CHECK(!img_output->ptr);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  // Load image into buffer
  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  const int retries = 100;
  for (int i = 0; i < retries; i++) {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_mmap.StartTransfer();

    memwriter_read.WaitForCompletion();
    memreader_mmap.WaitForCompletion();
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  double average = duration.count() / (double)retries;
  std::cout << "It took " << average << " in average" << std::endl;
  std::cout << "Equals to " << 1/average << " frame per second" << std::endl;

  BOOST_CHECK(CheckHash(img_output));

  output_file_stream.write(img_output->ptr, img_output->image_size);
}

/** Tests write + read */
BOOST_AUTO_TEST_CASE(memory_loop_case_read_write) {
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_TRUE);
  //as_reader_writer_reset(AS_MODULE_BASEADDR_READER0);
  //as_reader_writer_reset(AS_MODULE_BASEADDR_WRITER0);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderWrite memreader_write(memreader_input_write, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_write.GetImage();
  memreader_write.SetImageSize(1280*960);
  memreader_write.Open();
  BOOST_CHECK(memreader_write.GetIsOpen());
  BOOST_CHECK(img->ptr);

  cMemWriterRead memwriter_read(memwriter_output_read, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  BOOST_CHECK(!img_output->ptr);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  // Load image into buffer
  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  const int retries = 100;
  for (int i = 0; i < retries; i++) {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_write.StartTransfer();

    while (!memwriter_read.IsTransferComplete()) {
      bool bSuccess = Utilities::ReadOnce(memwriter_read);
      if (!bSuccess)
        break;
      bSuccess = Utilities::WriteOnce(memreader_write);
      if (!bSuccess)
        break;
    }
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  double average = duration.count() / (double)retries;
  std::cout << "It took " << average << " in average" << std::endl;
  std::cout << "Equals to " << 1/average << " frame per second" << std::endl;

  BOOST_CHECK(CheckHash(img_output));

  output_file_stream.write(img_output->ptr, img_output->image_size);
}

/** Tests mmap (non-ioctl) write + read */
BOOST_AUTO_TEST_CASE(memory_loop_multiple_mmap_write_read) {
  // Needed for regio access
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_TRUE);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderMmapWrite memreader_mmap(memreader_input_mmap, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_mmap.GetImage();
  BOOST_CHECK(!img->ptr);
  memreader_mmap.Open();
  BOOST_CHECK(!img->ptr);
  memreader_mmap.SetImageSize(1280*960);
  memreader_mmap.Open();
  BOOST_CHECK(img->ptr);

  cMemWriterRead memwriter_read(memwriter_output_read, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  BOOST_CHECK(!img_output->ptr);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  // Load image into buffer
  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  const int retries = 100;
  for (int i = 0; i < retries; i++) {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_mmap.StartTransfer();

    memwriter_read.WaitForCompletion();
    memreader_mmap.WaitForCompletion();
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  double average = duration.count() / (double)retries;
  std::cout << "It took " << average << " in average" << std::endl;
  std::cout << "Equals to " << 1/average << " frame per second" << std::endl;

  BOOST_CHECK(CheckHash(img_output));

  output_file_stream.write(img_output->ptr, img_output->image_size);
}

/** mmap read + write */
BOOST_AUTO_TEST_CASE(memory_loop_multiple_mmap_read_write) {
  // Needed for regio access
  as_support_init();

  as_invert_enable(AS_MODULE_BASEADDR_AS_INVERT_0, AS_TRUE);

  std::ifstream input_file_stream;
  input_file_stream.open(input_file, std::ios::binary);
  BOOST_CHECK(input_file_stream.is_open());

  std::ofstream output_file_stream;
  output_file_stream.open(output_file, std::ios::binary);
  BOOST_CHECK(output_file_stream.is_open());

  cMemReaderWrite memreader_mmap(memreader_input_write, AS_MODULE_BASEADDR_READER0);
  Image *img = memreader_mmap.GetImage();
  BOOST_CHECK(!img->ptr);
  memreader_mmap.SetImageSize(1280*960);
  memreader_mmap.Open();
  BOOST_CHECK(memreader_mmap.GetIsOpen());
  BOOST_REQUIRE(img->ptr);

  cMemWriterMmapRead memwriter_read(memwriter_output_mmap, AS_MODULE_BASEADDR_WRITER0);
  Image *img_output = memwriter_read.GetImage();
  memwriter_read.SetImageSize(1280*960);
  BOOST_CHECK(!img_output->ptr);
  memwriter_read.Open();
  BOOST_CHECK(img_output->ptr);

  // Load image into buffer
  input_file_stream.read(img->ptr, img->image_size);

  std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
  const int retries = 100;
  for (int i = 0; i < retries; i++) {
    // Usually memwriter needs to be started first
    memwriter_read.StartTransfer();
    memreader_mmap.StartTransfer();

    while (!memwriter_read.IsTransferComplete()) {
      bool bSuccess = Utilities::ReadOnce(memwriter_read);
      if (!bSuccess)
        break;
      bSuccess = Utilities::WriteOnce(memreader_mmap);
      if (!bSuccess)
        break;
    }
  }
  std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> duration = std::chrono::duration_cast<std::chrono::duration<double>> (t2 - t1);

  double average = duration.count() / (double)retries;
  std::cout << "It took " << average << " in average" << std::endl;
  std::cout << "Equals to " << 1/average << " frame per second" << std::endl;

  BOOST_CHECK(CheckHash(img_output));

  output_file_stream.write(img_output->ptr, img_output->image_size);
}

BOOST_AUTO_TEST_SUITE_END()
