"""Task 3 - RSA cryptosystem using cryptography and matplotlib."""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import hashes, serialization


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "report"
TIMING_CSV = DATA_DIR / "524K0008_524K0012_task3_timing.csv"
TIMING_GRAPH = REPORT_DIR / "524K0008_524K0012_task3_rsa_timing.png"
PRIVATE_KEY_PATH = DATA_DIR / "524K0008_524K0012_task3_rsa_private_key.pem"
PUBLIC_KEY_PATH = DATA_DIR / "524K0008_524K0012_task3_rsa_public_key.pem"


@dataclass(frozen=True)
class RSAKeyPair:
    private_key: RSAPrivateKey
    public_key: RSAPublicKey

    @property
    def key_size(self) -> int:
        return self.private_key.key_size

    @property
    def public_exponent(self) -> int:
        return self.public_key.public_numbers().e

    @property
    def modulus_bytes(self) -> int:
        return self.key_size // 8

    @property
    def max_plain_block_size(self) -> int:
        # OAEP overhead with SHA-256 is 2 * hash_len + 2 bytes.
        return self.modulus_bytes - (2 * hashes.SHA256().digest_size) - 2


@dataclass(frozen=True)
class CipherText:
    blocks: Tuple[bytes, ...]


def generate_keypair(bits: int = 2048) -> RSAKeyPair: #Generates an RSA key pair with the specified number of bits.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return RSAKeyPair(private_key=private_key, public_key=private_key.public_key())


def _oaep_padding() -> padding.OAEP: #Returns an OAEP padding object configured with MGF1 and SHA-256, which is used for RSA encryption and decryption.
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


def _chunk_bytes(data: bytes, size: int) -> Iterable[bytes]: #Splits the input byte data into chunks of the specified size.
    for start in range(0, len(data), size):
        yield data[start : start + size]


def encrypt_message(message: str, public_key: RSAPublicKey) -> CipherText: 
    key_size = public_key.key_size
    modulus_bytes = key_size // 8
    max_block_size = modulus_bytes - (2 * hashes.SHA256().digest_size) - 2
    if max_block_size <= 0:
        raise ValueError("RSA key is too small for OAEP with SHA-256.")

    blocks = tuple(
        public_key.encrypt(chunk, _oaep_padding())
        for chunk in _chunk_bytes(message.encode("utf-8"), max_block_size)
    )
    return CipherText(blocks=blocks)


def decrypt_message(ciphertext: CipherText, private_key: RSAPrivateKey) -> str:
    plain_chunks = [
        private_key.decrypt(block, _oaep_padding())
        for block in ciphertext.blocks
    ]
    return b"".join(plain_chunks).decode("utf-8")


def save_keys(keypair: RSAKeyPair) -> Tuple[Path, Path]: #Saves the RSA key pair to PEM files in the data directory and returns the paths to the private and public key files.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    private_bytes = keypair.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = keypair.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    PRIVATE_KEY_PATH.write_bytes(private_bytes)
    PUBLIC_KEY_PATH.write_bytes(public_bytes)
    return PRIVATE_KEY_PATH, PUBLIC_KEY_PATH


def verify_message(message: str, keypair: RSAKeyPair) -> Tuple[CipherText, str, bool]:
    ciphertext = encrypt_message(message, keypair.public_key)
    decrypted = decrypt_message(ciphertext, keypair.private_key)
    return ciphertext, decrypted, decrypted == message


SAMPLE_MESSAGES = [
    "Hi",
    "RSA",
    "Discrete Structures",
    "Truth table and predicate logic",
    "A short plaintext message for RSA testing.",
    "Student group 524K0008 and 524K0012 verifies encryption.",
    "RSA with OAEP padding is probabilistic and safer than textbook RSA.",
    "This message is intentionally longer to require chunking with the RSA modulus size.",
    "Vietnam International University - School of Computer Science and Engineering.",
    "The final sample message contains enough characters to test different plaintext lengths and correctness.",
]


def run_sample_tests(keypair: RSAKeyPair) -> List[Tuple[str, int, int, bool]]:
    results = []
    for message in SAMPLE_MESSAGES:
        ciphertext, decrypted, ok = verify_message(message, keypair)
        results.append((message, len(message.encode("utf-8")), len(ciphertext.blocks), ok))
        if decrypted != message:
            raise AssertionError("RSA verification failed.")
    return results


def measure_timings(keypair: RSAKeyPair, repeats: int = 20) -> List[Tuple[int, float, float]]:
    lengths = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    timings: List[Tuple[int, float, float]] = []

    for length in lengths:
        message = ("RSA timing test with cryptography OAEP " * ((length // 36) + 1))[:length]
        encrypt_total = 0.0
        decrypt_total = 0.0

        for _ in range(repeats):
            start = time.perf_counter()
            ciphertext = encrypt_message(message, keypair.public_key)
            encrypt_total += time.perf_counter() - start

            start = time.perf_counter()
            decrypted = decrypt_message(ciphertext, keypair.private_key)
            decrypt_total += time.perf_counter() - start

            if decrypted != message:
                raise AssertionError("Timing verification failed.")

        timings.append((length, encrypt_total / repeats, decrypt_total / repeats))

    return timings


def save_timing_csv(timings: Sequence[Tuple[int, float, float]], path: Path = TIMING_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["PlaintextLength", "EncryptionSeconds", "DecryptionSeconds"])
        writer.writerows(timings)
    return path


def draw_timing_graph(timings: Sequence[Tuple[int, float, float]], path: Path = TIMING_GRAPH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lengths = [row[0] for row in timings]
    encryption = [row[1] for row in timings]
    decryption = [row[2] for row in timings]

    plt.figure(figsize=(10, 6))
    plt.plot(lengths, encryption, marker="o", linewidth=2, label="Encryption")
    plt.plot(lengths, decryption, marker="s", linewidth=2, label="Decryption")
    plt.title("RSA Encryption/Decryption Time by Plaintext Length")
    plt.xlabel("Plaintext message length (characters)")
    plt.ylabel("Average time (seconds)")
    plt.grid(True, linestyle="--", alpha=0.45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path



def run_task3_demo() -> None:
    keypair = generate_keypair(bits=2048)
    private_path, public_path = save_keys(keypair)
    sample_results = run_sample_tests(keypair)
    timings = measure_timings(keypair)
    csv_path = save_timing_csv(timings)
    graph_path = draw_timing_graph(timings)

    print("TASK 3 - RSA CRYPTOSYSTEM")
    print("=" * 70)
    print("Library: cryptography")
    print("Padding: RSA-OAEP with SHA-256")
    print(f"Key size: {keypair.key_size} bits")
    print(f"Public exponent e: {keypair.public_exponent}")
    print(f"Maximum plaintext block size: {keypair.max_plain_block_size} bytes")
    print(f"Private key saved to: {private_path}")
    print(f"Public key saved to: {public_path}")

    print("\n10 sample-message tests:")
    for index, (message, byte_length, block_count, ok) in enumerate(sample_results, start=1):
        preview = message if len(message) <= 54 else message[:51] + "..."
        print(f"{index:02d}. length={byte_length:3d} bytes, blocks={block_count:2d}, verified={ok} | {preview}")

    print("\nTiming results:")
    print("Length | Encryption(s) | Decryption(s)")
    print("-------+---------------+--------------")
    for length, enc_time, dec_time in timings:
        print(f"{length:6d} | {enc_time:13.8f} | {dec_time:12.8f}")

    print(f"\nTiming CSV saved to: {csv_path}")
    print(f"Timing graph saved to: {graph_path}")


if __name__ == "__main__":
    run_task3_demo()
