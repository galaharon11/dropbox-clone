// try.cpp : This file contains the 'main' function. Program execution begins and ends there.
//
#define _CRT_SECURE_NO_WARNINGS
#define COBNMACROS

#include <windows.h>
#include <shellapi.h>
#include <shlobj_core.h>
#include <iostream>
#include <stdio.h>
#include <commonControls.h>
#include <commCtrl.h>
#pragma comment(linker, "/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")
#pragma comment(lib, "Shell32.lib")
#pragma comment(lib, "Comctl32.lib")

IImageList* bigIconList;
HDC icon_hdc;

struct ICONDIRENTRY
{
    UCHAR nWidth;
    UCHAR nHeight;
    UCHAR nNumColorsInPalette; // 0 if no palette
    UCHAR nReserved; // should be 0
    WORD nNumColorPlanes; // 0 or 1
    WORD nBitsPerPixel;
    ULONG nDataLength; // length in bytes
    ULONG nOffset; // offset of BMP or PNG data from beginning of file
};

struct ICONDIR
{
    short reserved;
    short type;
    short numOfIcons;
};

#define COLORBITS 32

HICON GetHICONFromExtension(const char* extension, bool getJumbo)
{
    SHFILEINFOA sfi;
    HICON icon;
    HRESULT hr;

    unsigned int flags = SHGFI_SYSICONINDEX | SHGFI_USEFILEATTRIBUTES;
    // If the user typed "directory", define the file attribute as a directory to get directory icon
    unsigned int fileAttribute = std::strcmp(extension, ".directory") ? FILE_ATTRIBUTE_NORMAL : FILE_ATTRIBUTE_DIRECTORY;
    unsigned int sizeFlag = getJumbo ? SHIL_JUMBO : SHIL_EXTRALARGE;

    hr = SHGetFileInfoA(extension, fileAttribute, &sfi, sizeof(sfi), flags);
    SHGetImageList(sizeFlag, IID_IImageList, (void**)&bigIconList);
    bigIconList->GetIcon(sfi.iIcon, 0, &icon);
    bigIconList->Release();
    return icon;
}

BOOL checkZero(BYTE arr[], int size) {
    for (int i = 0; i < size; i++) {
        if (arr[i] != 0) {
            return false;
        }
    }
    return true;
}
int SaveIcon(HICON icon, const char* filePath, bool truncate) {
    HRESULT hr;

    // create and open a icon file
    int createFlag = truncate ? TRUNCATE_EXISTING : CREATE_ALWAYS;
    HANDLE ico_file = CreateFileA(filePath, FILE_APPEND_DATA | GENERIC_WRITE, FILE_SHARE_WRITE | FILE_SHARE_READ, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (ico_file == INVALID_HANDLE_VALUE) {
        return false;
    }

    // Write ICONDIR struct (ICO header)
    ICONDIR ICOheader = { 0, 1, 1 };
    hr = WriteFile(ico_file, &ICOheader, sizeof(ICONDIR), NULL, NULL);
    hr = GetLastError();
    // Get information about the icon
    ICONINFO iconInfo;
    hr = GetIconInfo(icon, &iconInfo);


    BITMAPINFO bitmapInfo = { 0 };
    bitmapInfo.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmapInfo.bmiHeader.biBitCount = 0; // don't get the color table 
    // Get bitmap header from HICON
    hr = GetDIBits(GetDC(NULL), iconInfo.hbmColor, 0, 0, NULL, &bitmapInfo, DIB_RGB_COLORS);

    int nBmInfoSize = sizeof(BITMAPINFOHEADER);

    // Get bitmap bytes
    BYTE* bits = new BYTE[bitmapInfo.bmiHeader.biSizeImage];
    bitmapInfo.bmiHeader.biBitCount = COLORBITS;
    bitmapInfo.bmiHeader.biCompression = BI_RGB;
    if (!truncate) {
        hr = GetDIBits(GetDC(NULL), iconInfo.hbmColor, 49, 100, bits, &bitmapInfo, DIB_RGB_COLORS);
        if (checkZero(bits, 100 * 256 * 4)) {
            // If all bits between row 49 and row 149 are zeros, this icon is most likely does not support JUMBO icons (256*256).
            // If that is the case, return error code 2 to get the EXTRALARGE version of this icon.
            DestroyIcon(icon);
            CloseHandle(ico_file);

            DeleteObject(iconInfo.hbmColor);
            DeleteObject(iconInfo.hbmMask);

            delete[] bits;
            return 2;
        }
    }

    hr = GetDIBits(GetDC(NULL), iconInfo.hbmColor, 0, bitmapInfo.bmiHeader.biHeight, bits, &bitmapInfo, DIB_RGB_COLORS);

    // Get mask data
    BITMAPINFO maskInfo = { 0 };
    maskInfo.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    maskInfo.bmiHeader.biBitCount = 0;  // don't get the color table     
    hr = GetDIBits(GetDC(NULL), iconInfo.hbmMask, 0, 0, NULL, &maskInfo, DIB_RGB_COLORS);


    BYTE* maskBits = new BYTE[maskInfo.bmiHeader.biSizeImage];
    BYTE* maskInfoBytes = new BYTE[sizeof(BITMAPINFO) + maskInfo.bmiHeader.biClrUsed * sizeof(RGBQUAD)]; // Variable sized struct
    BITMAPINFO* pMaskInfo = (BITMAPINFO*)maskInfoBytes;
    memcpy(pMaskInfo, &maskInfo, sizeof(maskInfo));
    hr = GetDIBits(GetDC(NULL), iconInfo.hbmMask, 0, maskInfo.bmiHeader.biHeight, maskBits, pMaskInfo, DIB_RGB_COLORS);

    // Write directory entry (image header of ICO file)
    ICONDIRENTRY dir;
    dir.nWidth = (BYTE)bitmapInfo.bmiHeader.biWidth;
    dir.nHeight = (BYTE)bitmapInfo.bmiHeader.biHeight;
    dir.nNumColorsInPalette = 0;
    dir.nReserved = 0;
    dir.nNumColorPlanes = 0;
    dir.nBitsPerPixel = bitmapInfo.bmiHeader.biBitCount;
    dir.nDataLength = bitmapInfo.bmiHeader.biSizeImage + pMaskInfo->bmiHeader.biSizeImage + nBmInfoSize;
    dir.nOffset = sizeof(dir) + sizeof(ICONDIR);

    hr = WriteFile(ico_file, &dir, sizeof(dir), NULL, NULL);

    // Write DIB header (including color table). A DIB header is associated with bitmaps
    int nBitsSize = bitmapInfo.bmiHeader.biSizeImage;
    bitmapInfo.bmiHeader.biHeight *= 2; // because the header is for both image and mask
    bitmapInfo.bmiHeader.biCompression = 0;
    bitmapInfo.bmiHeader.biSizeImage += pMaskInfo->bmiHeader.biSizeImage; // because the header is for both image and mask
    hr = WriteFile(ico_file, &bitmapInfo.bmiHeader, nBmInfoSize, NULL, NULL);

    // Write image data:
    hr = WriteFile(ico_file, (BYTE*)bits, nBitsSize, NULL, NULL);

    // Write mask data:
    hr = WriteFile(ico_file, (BYTE*)maskBits, pMaskInfo->bmiHeader.biSizeImage, NULL, NULL);
    hr = GetLastError();

    DestroyIcon(icon);
    CloseHandle(ico_file);

    DeleteObject(iconInfo.hbmColor);
    DeleteObject(iconInfo.hbmMask);
    
    delete[] maskBits;
    delete[] maskInfoBytes;
    delete[] bits;


    return true;
}

wchar_t* char_to_wchar(char* str) {
    std::string normal(str);
    std::wstring wide(normal.begin(), normal.end());
    wchar_t* wideOnHeap = new wchar_t[wide.length()+1];
    std::wcscpy(wideOnHeap, wide.c_str());
    return(wideOnHeap);
}


void ExitError() {
    printf("Error");
    exit(0);
}


int main(int argc, char* argv[])
{
    if (argc > 1) {
        if (!strcmp(argv[1], "--help")) {
            printf("This program will save a .ico file of the icon associated with a specific extension\n"
                "Usage: GetIcon <icon-size> <path> <extension>\n"
                "icon-size: the size of the .ico file in pixels. Recommanded values are between 16 and 64\n"
                "path: the absolute path to a directory for saving the .ico file. The name of the file will be extension.ico (e.g. exe.ico, jpg.ico)\n"
                "extension: the extension to extract (e.g txt, png). The extension \"directory\" will be used to save directory icon\n"
                "It is possible to specify several extension at once.\n\n"
                "Example: GetIcon 64 C:/path/to/dir exe gif docx txt cpp\n");
            exit(0);
        }
    }
    if (argc < 4) {
        printf("Usage: GetIcon <icon-size> <path> <extensions>\n"
            "GetIcon --help for help\n");
        exit(0);

    }

    CoInitialize(NULL);

    HRESULT hr;
    HICON scaledIcon;
    HICON icon;

    int iconSize = atoi(argv[1]);
    char* path = argv[2];

    for (int i = 3; i < argc; i++) {
        char* extension = new char[2 + std::strlen(argv[i])];
        extension = std::strcpy(extension, ".\0");
        extension = std::strcat(extension, argv[i]);

        char* fileName = new char[5 + std::strlen(argv[i])];
        fileName = std::strcpy(fileName, (char*)argv[i]);
        fileName = std::strcat(fileName, ".ico");

        char* absPath = new char[std::strlen(path) + std::strlen(fileName) + 2];
        absPath = (char*)std::memcpy(absPath, path, std::strlen(path));
        absPath[std::strlen(path)] = '\\';
        absPath[std::strlen(path) + 1] = 0;
        absPath = std::strcat(absPath, fileName);

        icon = GetHICONFromExtension(extension, true);
        if(icon == INVALID_HANDLE_VALUE) 
            ExitError();
        int error = SaveIcon(icon, absPath, false);
        if (error == 2) {
            icon = GetHICONFromExtension(extension, false);
            error = SaveIcon(icon, absPath, false);
        }
        if (error == 0)
            ExitError();
        const wchar_t* widePath = char_to_wchar(absPath);
        if (LoadIconWithScaleDown(NULL, widePath, iconSize, iconSize, &scaledIcon) != S_OK)
            ExitError();
        if (!SaveIcon(scaledIcon, absPath, true))
            ExitError();

        printf("%s\n", absPath);
        delete[] extension; 
        delete[] fileName;
        delete[] absPath;
        delete[] widePath;
    }
        

    CoUninitialize();
}


