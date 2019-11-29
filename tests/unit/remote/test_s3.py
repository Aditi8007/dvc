# -*- coding: utf-8 -*-
import pytest
from moto import mock_s3

from dvc.remote.s3 import RemoteS3


@pytest.fixture
def remote():
    """Returns a RemoteS3 connected to a bucket with the following structure:

        bucket
        ├── data
        │  ├── alice
        │  ├── alpha
        │  └── subdir
        │     ├── 1
        │     ├── 2
        │     └── 3
        ├── empty_dir
        ├── empty_file
        └── foo
    """
    with mock_s3():
        remote = RemoteS3(None, {"url": "s3://bucket", "region": "us-east-1"})
        s3 = remote.s3

        s3.create_bucket(Bucket="bucket")
        s3.put_object(Bucket="bucket", Key="empty_dir/")
        s3.put_object(Bucket="bucket", Key="empty_file", Body=b"")
        s3.put_object(Bucket="bucket", Key="foo", Body=b"foo")
        s3.put_object(Bucket="bucket", Key="data/alice", Body=b"alice")
        s3.put_object(Bucket="bucket", Key="data/alpha", Body=b"alpha")
        s3.put_object(Bucket="bucket", Key="data/subdir/1", Body=b"1")
        s3.put_object(Bucket="bucket", Key="data/subdir/2", Body=b"2")
        s3.put_object(Bucket="bucket", Key="data/subdir/3", Body=b"3")

        yield remote


def test_isdir(remote):
    test_cases = [
        (True, "data"),
        (True, "data/"),
        (True, "data/subdir"),
        (True, "empty_dir"),
        (False, "foo"),
        (False, "data/alice"),
        (False, "data/al"),
        (False, "data/subdir/1"),
    ]

    for expected, path in test_cases:
        assert remote.isdir(remote.path_info / path) == expected


def test_exists(remote):
    test_cases = [
        (True, "data"),
        (True, "data/"),
        (True, "data/subdir"),
        (True, "empty_dir"),
        (True, "empty_file"),
        (True, "foo"),
        (True, "data/alice"),
        (True, "data/subdir/1"),
        (False, "data/al"),
        (False, "foo/"),
    ]

    for expected, path in test_cases:
        assert remote.exists(remote.path_info / path) == expected


def test_walk_files(remote):
    files = [
        remote.path_info / "data/alice",
        remote.path_info / "data/alpha",
        remote.path_info / "data/subdir/1",
        remote.path_info / "data/subdir/2",
        remote.path_info / "data/subdir/3",
        remote.path_info / "empty_file",
        remote.path_info / "foo",
    ]

    assert list(remote.walk_files(remote.path_info)) == files


def test_copy_preserve_etag_across_buckets(remote):
    s3 = remote.s3
    s3.create_bucket(Bucket="another")

    another = RemoteS3(None, {"url": "s3://another", "region": "us-east-1"})

    from_info = remote.path_info / "foo"
    to_info = another.path_info / "foo"

    remote.copy(from_info, to_info)

    from_etag = RemoteS3.get_etag(s3, "bucket", "foo")
    to_etag = RemoteS3.get_etag(s3, "another", "foo")

    assert from_etag == to_etag


def makedirs(remote):
    empty_dir = remote.path_info / "empty_dir"
    remote.remove(empty_dir)
    assert not remote.exists(empty_dir)
    remote.makedirs(empty_dir)
    assert remote.exists(empty_dir)
